from bson.codec_options import TypeDecoder, TypeRegistry, CodecOptions
from bson.int64 import Int64

# Haha, yeah AI helped write basically 100% of this.


class Int64ToIntDecoder(TypeDecoder):
    python_type = int  # The Python type you want to produce
    bson_type = Int64  # The BSON type you want to decode

    def transform_bson(self, value):
        return int(value)


codec_options = CodecOptions(
    type_registry=TypeRegistry([Int64ToIntDecoder()]))
