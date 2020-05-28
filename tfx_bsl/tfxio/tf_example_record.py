# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""TFXIO implementation for tf.Example records."""

from __future__ import absolute_import
from __future__ import division
# Standard __future__ imports
from __future__ import print_function

import abc

from absl import logging
import apache_beam as beam
import pyarrow as pa
import six
from tfx_bsl.coders import batch_util
from tfx_bsl.coders import example_coder
from tfx_bsl.tfxio import record_based_tfxio
from tfx_bsl.tfxio import tensor_adapter
from tfx_bsl.tfxio import tensor_representation_util
from tfx_bsl.tfxio import tfxio
from typing import List, Optional, Text

from tensorflow_metadata.proto.v0 import schema_pb2


@six.add_metaclass(abc.ABCMeta)
class _TFExampleRecordBase(record_based_tfxio.RecordBasedTFXIO):
  """Base class for TFXIO implementations for record based tf.Examples."""

  def __init__(self,
               schema: Optional[schema_pb2.Schema] = None,
               raw_record_column_name: Optional[Text] = None,
               telemetry_descriptors: Optional[List[Text]] = None,
               physical_format: Optional[Text] = None,
               schema_for_decoding: Optional[schema_pb2.Schema] = None):
    # TODO(b/154648951): make telemetry_descriptors and physical_format required
    # arguments, when TFT's compatibility TFXIO starts setting them.
    if physical_format is None:
      physical_format = "unknown"
    super(_TFExampleRecordBase, self).__init__(
        telemetry_descriptors=telemetry_descriptors,
        raw_record_column_name=raw_record_column_name,
        logical_format="tf_example",
        physical_format=physical_format)
    self._schema = schema
    if self._can_produce_large_types:
      logging.info("We decided to produce LargeList and LargeBinary types.")
    if schema_for_decoding is not None:
      assert schema is not None
    self._schema_for_decoding = schema_for_decoding

  def SupportAttachingRawRecords(self) -> bool:
    return True

  @abc.abstractmethod
  def _RawRecordBeamSourceInternal(self) -> beam.PTransform:
    """Returns a PTransform that produces PCollection[bytes]."""

  def _RawRecordToRecordBatchInternal(self,
                                      batch_size: Optional[int] = None
                                     ) -> beam.PTransform:

    @beam.typehints.with_input_types(bytes)
    @beam.typehints.with_output_types(pa.RecordBatch)
    def _PTransformFn(raw_records_pcoll: beam.pvalue.PCollection):
      return (raw_records_pcoll
              | "Batch" >> beam.BatchElements(
                  **batch_util.GetBatchElementsKwargs(batch_size))
              | "Decode" >> beam.ParDo(
                  _DecodeBatchExamplesDoFn(self._GetSchemaForDecoding(),
                                           self.raw_record_column_name,
                                           self._can_produce_large_types)))

    return beam.ptransform_fn(_PTransformFn)()

  def _ArrowSchemaNoRawRecordColumn(self) -> pa.Schema:
    schema = self._GetSchemaForDecoding()
    if schema is None:
      raise ValueError("TFMD schema not provided. Unable to derive an"
                       "Arrow schema")
    return example_coder.ExamplesToRecordBatchDecoder(
        schema.SerializeToString(),
        self._can_produce_large_types).ArrowSchema()

  def TensorRepresentations(self) -> tensor_adapter.TensorRepresentations:
    result = (
        tensor_representation_util.GetTensorRepresentationsFromSchema(
            self._schema))
    if result is None:
      result = (
          tensor_representation_util.InferTensorRepresentationsFromSchema(
              self._schema))
    return result

  def _ProjectTfmdSchema(self, tensor_names: List[Text]) -> schema_pb2.Schema:
    """Projects self._schema by the given tensor names."""
    tensor_representations = self.TensorRepresentations()
    tensor_names = set(tensor_names)
    if not tensor_names.issubset(tensor_representations):
      raise ValueError(
          "Unable to project {} because they were not in the original "
          "TensorRepresentations.".format(tensor_names -
                                          tensor_representations))
    columns = set()
    for tensor_name in tensor_names:
      columns.update(
          tensor_representation_util.GetSourceColumnsFromTensorRepresentation(
              tensor_representations[tensor_name]))
    result = schema_pb2.Schema()
    # Note: We only copy projected features into the new schema because the
    # coder, and ArrowSchema() only care about Schema.feature. If they start
    # depending on other Schema fields then those fields must also be projected.
    for f in self._schema.feature:
      if f.name in columns:
        result.feature.add().CopyFrom(f)

    tensor_representation_util.SetTensorRepresentationsInSchema(
        result,
        {k: v for k, v in tensor_representations.items() if k in tensor_names})

    return result

  def _GetSchemaForDecoding(self) -> schema_pb2.Schema:
    return (self._schema
            if self._schema_for_decoding is None else self._schema_for_decoding)


class TFExampleRecord(_TFExampleRecordBase):
  """TFXIO implementation for tf.Example on TFRecord."""

  def __init__(self,
               file_pattern: Text,
               validate: bool = True,
               schema: Optional[schema_pb2.Schema] = None,
               raw_record_column_name: Optional[Text] = None,
               telemetry_descriptors: Optional[List[Text]] = None):
    """Initializes a TFExampleRecord TFXIO.

    Args:
      file_pattern: A file glob pattern to read TFRecords from.
      validate: Boolean flag to verify that the files exist during the pipeline
        creation time.
      schema: A TFMD Schema describing the dataset.
      raw_record_column_name: If not None, the generated Arrow RecordBatches
        will contain a column of the given name that contains serialized
        records.
      telemetry_descriptors: A set of descriptors that identify the component
        that is instantiating this TFXIO. These will be used to construct the
        namespace to contain metrics for profiling and are therefore expected to
        be identifiers of the component itself and not individual instances of
        source use.
    """
    super(TFExampleRecord, self).__init__(
        schema=schema, raw_record_column_name=raw_record_column_name,
        telemetry_descriptors=telemetry_descriptors,
        physical_format="tfrecords_gzip")
    self._file_pattern = file_pattern
    self._validate = validate

  def _RawRecordBeamSourceInternal(self) -> beam.PTransform:
    return beam.io.ReadFromTFRecord(self._file_pattern, validate=self._validate)

  def _ProjectImpl(self, tensor_names: List[Text]) -> tfxio.TFXIO:
    projected_schema = self._ProjectTfmdSchema(tensor_names)
    return TFExampleRecord(
        file_pattern=self._file_pattern,
        validate=self._validate,
        schema=projected_schema,
        raw_record_column_name=self.raw_record_column_name,
        telemetry_descriptors=self.telemetry_descriptors)

  def TensorFlowDataset(self):
    raise NotImplementedError


@beam.typehints.with_input_types(List[bytes])
@beam.typehints.with_output_types(pa.RecordBatch)
class _DecodeBatchExamplesDoFn(beam.DoFn):
  """Batches serialized protos bytes and decode them into an Arrow table."""

  def __init__(self, schema: Optional[schema_pb2.Schema],
               raw_record_column_name: Optional[Text],
               produce_large_types: bool):
    """Initializer."""
    self._schema = schema
    self._raw_record_column_name = raw_record_column_name
    self._decoder = None
    self._produce_large_types = produce_large_types

  def setup(self):
    if self._schema:
      self._decoder = example_coder.ExamplesToRecordBatchDecoder(
          self._schema.SerializeToString(),
          self._produce_large_types)
    else:
      self._decoder = example_coder.ExamplesToRecordBatchDecoder(
          self._produce_large_types)

  def process(self, examples: List[bytes]):
    decoded = self._decoder.DecodeBatch(examples)
    if self._raw_record_column_name is None:
      yield decoded
    else:
      yield record_based_tfxio.AppendRawRecordColumn(
          decoded, self._raw_record_column_name, examples,
          self._produce_large_types)
