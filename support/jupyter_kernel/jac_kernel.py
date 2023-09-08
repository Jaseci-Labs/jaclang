import contextlib
import os
import os.path as op
import tempfile
from io import StringIO

from ipykernel.kernelapp import IPKernelApp
from ipykernel.kernelbase import Kernel

from jaclang import jac_blue_import as jac_import

from pygments import lexer

from syntax_hilighter import JacLexer

"""Register the lexer."""
lexer.add_lexer("jac_lexer", JacLexer())


def exec_jac(code: str):
    """Compile, jac code, and return the standard py."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # define the source and executable filenames. temp.jac is the file that we want to execute.
        source_path = op.join(tmpdir, "temp.jac")

        # Write the code to the jac file.
        with open(source_path, "w") as f:
            f.write(code)

        try:
            jac_import(
                op.join(tmpdir, "temp")
            )  # import the jac file, this generates the __jac_gen__ folder at the same level as the jac file,
            # this folder contains the python file that we want to execute.

        except Exception as e:
            captured_output = "Exception: " + str(e)
            return captured_output

        finally:
            pass

    script_path = op.join(os.getcwd(), "jac/__jac_gen__/temp.py")

    try:
        with open(script_path, "r") as script_file:
            script_code = script_file.read()
            stdout_capture = StringIO()  # You need to import StringIO from io module

            with contextlib.redirect_stdout(stdout_capture):
                exec(script_code)

            captured_output = stdout_capture.getvalue()

    except Exception as e:
        captured_output = "Exception: " + str(e)

    return captured_output


class JacKernel(Kernel):
    """Jac wrapper kernel."""

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

            finally:
                pass

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
