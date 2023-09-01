import os
import os.path as op
import tempfile
import subprocess

from ipykernel.kernelbase import Kernel
from ipykernel.kernelapp import IPKernelApp
from jaclang import jac_purple_import as jac_import

from pygments import lexer
from syntax_hilighter import JacLexer

lexer.add_lexer("jac_lexer", JacLexer())


def exec_jac(code):
    """Compile, jac code, and return the standard py."""

    with tempfile.TemporaryDirectory() as tmpdir:
        # define the source and executable filenames. temp.jac is the file that we want to execute.
        source_path = op.join(tmpdir, "temp.jac")

        # Write the code to the jac file.
        with open(source_path, "w") as f:
            f.write(code)

        jac_import(
            op.join(tmpdir, "temp")
        )  # import the jac file, this generates the __jac_gen__ folder at the same level as the jac file,
        # this folder contains the python file that we want to execute, I want to execute the file that is named temp.py.

    script_path = op.join(os.getcwd(), "jac/__jac_gen__/temp.py")

    output = os.popen("python {0:s}".format(script_path)).read()

    if "Traceback" in output:
        # Extract the exception message from the output
        lines = output.splitlines()
        exception_message = ""
        exception_found = False

        for line in lines:
            if line.startswith("Traceback"):
                exception_found = True
                exception_message = line
            elif exception_found and line.strip() != "":
                exception_message += "\n" + line

        return exception_message
    else:
        # No exception occurred
        return output


"""Jac wrapper kernel."""


class JacKernel(Kernel):
    # Kernel information.
    implementation = "jac"
    implementation_version = "0.0"
    language = "python"  # for syntax hilighting
    language_version = "1.0"
    language_info = {
        "name": "python",
        "mimetype": "text/plain",
        "pygments_lexer": "jac_lexer",
        "file_extension": ".jac",
    }

    banner = "Jac kernel for Jupyter (main), version 1.0.0a4\n\n"

    def do_execute(
        self,
        code,
        silent,
        store_history=True,
        user_expressions=None,
        allow_stdin=False,
        stop_on_error=False,
    ):
        """called when a code cell is executed."""
        if not silent:
            try:
                output = exec_jac(code)
                # send back the result to the frontend.
                stream_content = {"name": "stdout", "text": output}
                self.send_response(self.iopub_socket, "stream", stream_content)
            except Exception as e:
                # Send the exception as an error message to the frontend.
                error_content = {
                    "ename": type(e).__name__,
                    "evalue": str(e),
                    "traceback": [],
                }
                self.send_response(self.iopub_socket, "error", error_content)

                return {
                    "status": "error",
                    "execution_count": self.execution_count,
                }

        # return the execution result.
        return {
            "status": "ok",
            # The base class increments the execution
            # count
            "execution_count": self.execution_count,
            "payload": [],
            "user_expressions": {},
        }


if __name__ == "__main__":
    IPKernelApp.launch_instance(kernel_class=JacKernel)
