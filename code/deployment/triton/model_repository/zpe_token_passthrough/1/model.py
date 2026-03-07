import numpy as np
import triton_python_backend_utils as pb_utils


class TritonPythonModel:
    def initialize(self, args):
        del args

    def execute(self, requests):
        responses = []
        for request in requests:
            token_ids = pb_utils.get_input_tensor_by_name(request, "token_ids")
            output = pb_utils.Tensor(
                "token_ids_out",
                np.asarray(token_ids.as_numpy(), dtype=np.int64),
            )
            responses.append(pb_utils.InferenceResponse(output_tensors=[output]))
        return responses
