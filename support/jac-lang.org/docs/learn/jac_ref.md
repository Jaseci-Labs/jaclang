# Jac Language Reference

--8<-- "examples/reference/introduction.md"

## Base Module structure
**Grammar Snippet**
```yaml linenums="2"
--8<-- "jaclang/compiler/jac.lark:2:17"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/base_module_structure.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/base_module_structure.py"
    ```
**Description**

--8<-- "examples/reference/base_module_structure.md"

## Import/Include Statements
**Grammar Snippet**
```yaml linenums="20"
--8<-- "jaclang/compiler/jac.lark:20:30"
--8<-- "jaclang/compiler/jac.lark:20:30"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/import_include_statements.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/import_include_statements.py"
    ```
**Description**

--8<-- "examples/reference/import_include_statements.md"

## Architypes
**Grammar Snippet**
```yaml linenums="33"
--8<-- "jaclang/compiler/jac.lark:33:46"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/architypes.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/architypes.py"
    ```
**Description**

--8<-- "examples/reference/architypes.md"

## Architype bodies
**Grammar Snippet**
```yaml linenums="49"
--8<-- "jaclang/compiler/jac.lark:49:54"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/architype_bodies.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/architype_bodies.py"
    ```
**Description**

--8<-- "examples/reference/architype_bodies.md"

## Enumerations
**Grammar Snippet**
```yaml linenums="57"
--8<-- "jaclang/compiler/jac.lark:57:67"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/enumerations.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/enumerations.py"
    ```
**Description**

--8<-- "examples/reference/enumerations.md"

## Abilities
**Grammar Snippet**
```yaml linenums="70"
--8<-- "jaclang/compiler/jac.lark:70:81"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/abilities.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/abilities.py"
    ```
**Description**

--8<-- "examples/reference/abilities.md"

## Global variables
**Grammar Snippet**
```yaml linenums="84"
--8<-- "jaclang/compiler/jac.lark:84:85"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/global_variables.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/global_variables.py"
    ```
**Description**

--8<-- "examples/reference/global_variables.md"

## Free code
**Grammar Snippet**
```yaml linenums="88"
--8<-- "jaclang/compiler/jac.lark:88:88"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/free_code.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/free_code.py"
    ```
**Description**

--8<-- "examples/reference/free_code.md"

## Inline python
**Grammar Snippet**
```yaml linenums="91"
--8<-- "jaclang/compiler/jac.lark:91:91"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/inline_python.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/inline_python.py"
    ```
**Description**

--8<-- "examples/reference/inline_python.md"

## Tests
**Grammar Snippet**
```yaml linenums="94"
--8<-- "jaclang/compiler/jac.lark:94:94"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/tests.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/tests.py"
    ```
**Description**

--8<-- "examples/reference/tests.md"

## Implementations
**Grammar Snippet**
```yaml linenums="97"
--8<-- "jaclang/compiler/jac.lark:97:114"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/implementations.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/implementations.py"
    ```
**Description**

--8<-- "examples/reference/implementations.md"

## Codeblocks and Statements
**Grammar Snippet**
```yaml linenums="117"
--8<-- "jaclang/compiler/jac.lark:117:144"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/codeblocks_and_statements.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/codeblocks_and_statements.py"
    ```
**Description**

--8<-- "examples/reference/codeblocks_and_statements.md"

## If statements
**Grammar Snippet**
```yaml linenums="147"
--8<-- "jaclang/compiler/jac.lark:147:149"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/if_statements.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/if_statements.py"
    ```
**Description**

--8<-- "examples/reference/if_statements.md"

## While statements
**Grammar Snippet**
```yaml linenums="152"
--8<-- "jaclang/compiler/jac.lark:152:152"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/while_statements.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/while_statements.py"
    ```
**Description**

--8<-- "examples/reference/while_statements.md"

## For statements
**Grammar Snippet**
```yaml linenums="155"
--8<-- "jaclang/compiler/jac.lark:155:156"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/for_statements.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/for_statements.py"
    ```
**Description**

--8<-- "examples/reference/for_statements.md"

## Try statements
**Grammar Snippet**
```yaml linenums="159"
--8<-- "jaclang/compiler/jac.lark:159:162"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/try_statements.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/try_statements.py"
    ```
**Description**

--8<-- "examples/reference/try_statements.md"

## Match statements
**Grammar Snippet**
```yaml linenums="165"
--8<-- "jaclang/compiler/jac.lark:165:166"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/match_statements.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/match_statements.py"
    ```
**Description**

--8<-- "examples/reference/match_statements.md"

## Match patterns
**Grammar Snippet**
```yaml linenums="169"
--8<-- "jaclang/compiler/jac.lark:169:179"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/match_patterns.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/match_patterns.py"
    ```
**Description**

--8<-- "examples/reference/match_patterns.md"

## Match litteral patterns
**Grammar Snippet**
```yaml linenums="182"
--8<-- "jaclang/compiler/jac.lark:182:182"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/match_litteral_patterns.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/match_litteral_patterns.py"
    ```
**Description**

--8<-- "examples/reference/match_litteral_patterns.md"

## Match singleton patterns
**Grammar Snippet**
```yaml linenums="185"
--8<-- "jaclang/compiler/jac.lark:185:185"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/match_singleton_patterns.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/match_singleton_patterns.py"
    ```
**Description**

--8<-- "examples/reference/match_singleton_patterns.md"

## Match capture patterns
**Grammar Snippet**
```yaml linenums="188"
--8<-- "jaclang/compiler/jac.lark:188:188"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/match_capture_patterns.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/match_capture_patterns.py"
    ```
**Description**

--8<-- "examples/reference/match_capture_patterns.md"

## Match sequence patterns
**Grammar Snippet**
```yaml linenums="191"
--8<-- "jaclang/compiler/jac.lark:191:192"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/match_sequence_patterns.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/match_sequence_patterns.py"
    ```
**Description**

--8<-- "examples/reference/match_sequence_patterns.md"

## Match mapping patterns
**Grammar Snippet**
```yaml linenums="195"
--8<-- "jaclang/compiler/jac.lark:195:197"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/match_mapping_patterns.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/match_mapping_patterns.py"
    ```
**Description**

--8<-- "examples/reference/match_mapping_patterns.md"

## Match class patterns
**Grammar Snippet**
```yaml linenums="200"
--8<-- "jaclang/compiler/jac.lark:200:204"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/match_class_patterns.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/match_class_patterns.py"
    ```
**Description**

--8<-- "examples/reference/match_class_patterns.md"

## Context managers
**Grammar Snippet**
```yaml linenums="207"
--8<-- "jaclang/compiler/jac.lark:207:209"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/context_managers.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/context_managers.py"
    ```
**Description**

--8<-- "examples/reference/context_managers.md"

## Global and nonlocal statements
**Grammar Snippet**
```yaml linenums="212"
--8<-- "jaclang/compiler/jac.lark:212:214"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/global_and_nonlocal_statements.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/global_and_nonlocal_statements.py"
    ```
**Description**

--8<-- "examples/reference/global_and_nonlocal_statements.md"

## Data spatial typed context blocks
**Grammar Snippet**
```yaml linenums="217"
--8<-- "jaclang/compiler/jac.lark:217:217"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/data_spatial_typed_context_blocks.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/data_spatial_typed_context_blocks.py"
    ```
**Description**

--8<-- "examples/reference/data_spatial_typed_context_blocks.md"

## Return statements
**Grammar Snippet**
```yaml linenums="220"
--8<-- "jaclang/compiler/jac.lark:220:220"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/return_statements.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/return_statements.py"
    ```
**Description**

--8<-- "examples/reference/return_statements.md"

## Yield statements
**Grammar Snippet**
```yaml linenums="223"
--8<-- "jaclang/compiler/jac.lark:223:223"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/yield_statements.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/yield_statements.py"
    ```
**Description**

--8<-- "examples/reference/yield_statements.md"

## Raise statements
**Grammar Snippet**
```yaml linenums="226"
--8<-- "jaclang/compiler/jac.lark:226:226"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/raise_statements.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/raise_statements.py"
    ```
**Description**

--8<-- "examples/reference/raise_statements.md"

## Assert statements
**Grammar Snippet**
```yaml linenums="229"
--8<-- "jaclang/compiler/jac.lark:229:229"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/assert_statements.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/assert_statements.py"
    ```
**Description**

--8<-- "examples/reference/assert_statements.md"

## Delete statements
**Grammar Snippet**
```yaml linenums="232"
--8<-- "jaclang/compiler/jac.lark:232:232"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/delete_statements.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/delete_statements.py"
    ```
**Description**

--8<-- "examples/reference/delete_statements.md"

## Report statements
**Grammar Snippet**
```yaml linenums="235"
--8<-- "jaclang/compiler/jac.lark:235:235"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/report_statements.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/report_statements.py"
    ```
**Description**

--8<-- "examples/reference/report_statements.md"

## Control statements
**Grammar Snippet**
```yaml linenums="238"
--8<-- "jaclang/compiler/jac.lark:238:238"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/control_statements.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/control_statements.py"
    ```
**Description**

--8<-- "examples/reference/control_statements.md"

## Llm type statements
**Grammar Snippet**
```yaml linenums="241"
--8<-- "jaclang/compiler/jac.lark:241:241"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/llm_type_statements.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/llm_type_statements.py"
    ```
**Description**

--8<-- "examples/reference/llm_type_statements.md"

## Data spatial Walker statements
**Grammar Snippet**
```yaml linenums="244"
--8<-- "jaclang/compiler/jac.lark:244:247"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/data_spatial_walker_statements.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/data_spatial_walker_statements.py"
    ```
**Description**

--8<-- "examples/reference/data_spatial_walker_statements.md"

## Visit statements
**Grammar Snippet**
```yaml linenums="250"
--8<-- "jaclang/compiler/jac.lark:250:250"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/visit_statements.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/visit_statements.py"
    ```
**Description**

--8<-- "examples/reference/visit_statements.md"

## Revisit statements
**Grammar Snippet**
```yaml linenums="253"
--8<-- "jaclang/compiler/jac.lark:253:253"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/revisit_statements.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/revisit_statements.py"
    ```
**Description**

--8<-- "examples/reference/revisit_statements.md"

## Disengage statements
**Grammar Snippet**
```yaml linenums="256"
--8<-- "jaclang/compiler/jac.lark:256:256"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/disengage_statements.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/disengage_statements.py"
    ```
**Description**

--8<-- "examples/reference/disengage_statements.md"

## Ignore statements
**Grammar Snippet**
```yaml linenums="259"
--8<-- "jaclang/compiler/jac.lark:259:259"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/ignore_statements.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/ignore_statements.py"
    ```
**Description**

--8<-- "examples/reference/ignore_statements.md"

## Assignments
**Grammar Snippet**
```yaml linenums="262"
--8<-- "jaclang/compiler/jac.lark:262:279"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/assignments.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/assignments.py"
    ```
**Description**

--8<-- "examples/reference/assignments.md"

## Expressions
**Grammar Snippet**
```yaml linenums="282"
--8<-- "jaclang/compiler/jac.lark:282:283"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/expressions.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/expressions.py"
    ```
**Description**

--8<-- "examples/reference/expressions.md"

## Walrus assignments
**Grammar Snippet**
```yaml linenums="286"
--8<-- "jaclang/compiler/jac.lark:286:286"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/walrus_assignments.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/walrus_assignments.py"
    ```
**Description**

--8<-- "examples/reference/walrus_assignments.md"

## Lambda expressions
**Grammar Snippet**
```yaml linenums="289"
--8<-- "jaclang/compiler/jac.lark:289:289"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/lambda_expressions.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/lambda_expressions.py"
    ```
**Description**

--8<-- "examples/reference/lambda_expressions.md"

## Pipe expressions
**Grammar Snippet**
```yaml linenums="292"
--8<-- "jaclang/compiler/jac.lark:292:292"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/pipe_expressions.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/pipe_expressions.py"
    ```
**Description**

--8<-- "examples/reference/pipe_expressions.md"

## Pipe back expressions
**Grammar Snippet**
```yaml linenums="295"
--8<-- "jaclang/compiler/jac.lark:295:295"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/pipe_back_expressions.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/pipe_back_expressions.py"
    ```
**Description**

--8<-- "examples/reference/pipe_back_expressions.md"

## Elvis expressions
**Grammar Snippet**
```yaml linenums="298"
--8<-- "jaclang/compiler/jac.lark:298:298"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/elvis_expressions.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/elvis_expressions.py"
    ```
**Description**

--8<-- "examples/reference/elvis_expressions.md"

## Bitwise expressions
**Grammar Snippet**
```yaml linenums="301"
--8<-- "jaclang/compiler/jac.lark:301:304"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/bitwise_expressions.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/bitwise_expressions.py"
    ```
**Description**

--8<-- "examples/reference/bitwise_expressions.md"

## Logical and compare expressions
**Grammar Snippet**
```yaml linenums="307"
--8<-- "jaclang/compiler/jac.lark:307:321"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/logical_and_compare_expressions.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/logical_and_compare_expressions.py"
    ```
**Description**

--8<-- "examples/reference/logical_and_compare_expressions.md"

## Arithmetic expressions
**Grammar Snippet**
```yaml linenums="324"
--8<-- "jaclang/compiler/jac.lark:324:327"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/arithmetic_expressions.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/arithmetic_expressions.py"
    ```
**Description**

--8<-- "examples/reference/arithmetic_expressions.md"

## Connect expressions
**Grammar Snippet**
```yaml linenums="330"
--8<-- "jaclang/compiler/jac.lark:330:330"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/connect_expressions.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/connect_expressions.py"
    ```
**Description**

--8<-- "examples/reference/connect_expressions.md"

## Atomic expressions
**Grammar Snippet**
```yaml linenums="333"
--8<-- "jaclang/compiler/jac.lark:333:333"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/atomic_expressions.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/atomic_expressions.py"
    ```
**Description**

--8<-- "examples/reference/atomic_expressions.md"

## Atomic pipe back expressions
**Grammar Snippet**
```yaml linenums="336"
--8<-- "jaclang/compiler/jac.lark:336:336"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/atomic_pipe_back_expressions.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/atomic_pipe_back_expressions.py"
    ```
**Description**

--8<-- "examples/reference/atomic_pipe_back_expressions.md"

## Data spatial spawn expressions
**Grammar Snippet**
```yaml linenums="339"
--8<-- "jaclang/compiler/jac.lark:339:339"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/data_spatial_spawn_expressions.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/data_spatial_spawn_expressions.py"
    ```
**Description**

--8<-- "examples/reference/data_spatial_spawn_expressions.md"

## Unpack expressions
**Grammar Snippet**
```yaml linenums="342"
--8<-- "jaclang/compiler/jac.lark:342:342"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/unpack_expressions.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/unpack_expressions.py"
    ```
**Description**

--8<-- "examples/reference/unpack_expressions.md"

## References (unused)
**Grammar Snippet**
```yaml linenums="345"
--8<-- "jaclang/compiler/jac.lark:345:345"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/references_(unused).jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/references_(unused).py"
    ```
**Description**

--8<-- "examples/reference/references_(unused).md"

## Data spatial calls
**Grammar Snippet**
```yaml linenums="348"
--8<-- "jaclang/compiler/jac.lark:348:348"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/data_spatial_calls.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/data_spatial_calls.py"
    ```
**Description**

--8<-- "examples/reference/data_spatial_calls.md"

## Subscripted and dotted expressions
**Grammar Snippet**
```yaml linenums="351"
--8<-- "jaclang/compiler/jac.lark:351:356"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/subscripted_and_dotted_expressions.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/subscripted_and_dotted_expressions.py"
    ```
**Description**

--8<-- "examples/reference/subscripted_and_dotted_expressions.md"

## Function calls
**Grammar Snippet**
```yaml linenums="359"
--8<-- "jaclang/compiler/jac.lark:359:363"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/function_calls.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/function_calls.py"
    ```
**Description**

--8<-- "examples/reference/function_calls.md"

## Atom
**Grammar Snippet**
```yaml linenums="366"
--8<-- "jaclang/compiler/jac.lark:366:388"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/atom.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/atom.py"
    ```
**Description**

--8<-- "examples/reference/atom.md"

## Collection values
**Grammar Snippet**
```yaml linenums="391"
--8<-- "jaclang/compiler/jac.lark:391:412"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/collection_values.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/collection_values.py"
    ```
**Description**

--8<-- "examples/reference/collection_values.md"

## Tuples and Jac Tuples
**Grammar Snippet**
```yaml linenums="415"
--8<-- "jaclang/compiler/jac.lark:415:422"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/tuples_and_jac_tuples.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/tuples_and_jac_tuples.py"
    ```
**Description**

--8<-- "examples/reference/tuples_and_jac_tuples.md"

## Data Spatial References
**Grammar Snippet**
```yaml linenums="425"
--8<-- "jaclang/compiler/jac.lark:425:434"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/data_spatial_references.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/data_spatial_references.py"
    ```
**Description**

--8<-- "examples/reference/data_spatial_references.md"

## Special Comprehensions
**Grammar Snippet**
```yaml linenums="437"
--8<-- "jaclang/compiler/jac.lark:437:442"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/special_comprehensions.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/special_comprehensions.py"
    ```
**Description**

--8<-- "examples/reference/special_comprehensions.md"

## Names and references
**Grammar Snippet**
```yaml linenums="445"
--8<-- "jaclang/compiler/jac.lark:445:459"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/names_and_references.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/names_and_references.py"
    ```
**Description**

--8<-- "examples/reference/names_and_references.md"

## Builtin types
**Grammar Snippet**
```yaml linenums="462"
--8<-- "jaclang/compiler/jac.lark:462:472"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/builtin_types.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/builtin_types.py"
    ```
**Description**

--8<-- "examples/reference/builtin_types.md"

## Lexer Tokens
**Grammar Snippet**
```yaml linenums="475"
--8<-- "jaclang/compiler/jac.lark:475:650"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/lexer_tokens.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/lexer_tokens.py"
    ```
**Description**

--8<-- "examples/reference/lexer_tokens.md"

## f-string tokens
**Grammar Snippet**
```yaml linenums="653"
--8<-- "jaclang/compiler/jac.lark:653:664"
```
**Code Example**
=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/reference/f_string_tokens.jac"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/reference/f_string_tokens.py"
    ```
**Description**

--8<-- "examples/reference/f_string_tokens.md"

