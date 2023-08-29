
import os
import os.path as op
import tempfile

from IPython.utils.process import getoutput
from ipykernel.kernelbase import Kernel
from ipykernel.kernelapp import IPKernelApp
from jaclang import jac_purple_import as jac_import

def exec_jac(code):
    """Compile, jac code, and return the standard py."""

    with tempfile.TemporaryDirectory() as tmpdir:

        # define the source and executable filenames. temp.jac is the file that we want to execute.
        source_path = op.join(tmpdir, 'temp.jac')

        # Write the code to the jac file.
        with open(source_path, 'w') as f:
            f.write(code)

        jac_import(op.join(tmpdir,'temp')) # import the jac file, this generates the __jac_gen__ folder at the same level as the jac file,
        # this folder contains the python file that we want to execute, I want to execute the file that is named temp.py. 

        script_path = op.join(os.getcwd(),'jac/__jac_gen__/temp.py')
        output = os.popen("python {0:s}".format(script_path)).read()

        return output
    
"""Jac wrapper kernel."""
class JacKernel(Kernel):

    # Kernel information.
    implementation = 'jac'
    implementation_version = '0.0'
    language = 'python' # for syntax hilighting
    language_version = '1.0'
    language_info = {'name': 'jac',
                        'mimetype': 'text/plain'}
    banner = "Jac kernel"

    def do_execute(self, code, silent,
                    store_history=True,
                    user_expressions=None,
                    allow_stdin=False):
        
        """called when a code cell is executed."""
        if not silent:

            output = exec_jac(code)

            #send back the result to the frontend.
            stream_content = {'name': 'stdout',
                                'text': output}
            self.send_response(self.iopub_socket,
                                'stream', stream_content)
        return {'status': 'ok',
                # The base class increments the execution
                # count
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': {},
                }

if __name__ == '__main__':
    IPKernelApp.launch_instance(kernel_class=JacKernel)
