# re2compiler
A compiler for a [regex coprocessor](https://github.com/DanieleParravicini/regex_coprocessor)

---------------------------------------
# How to start?
Very simple!

1. clone this repo
2. run `pip install -r requirements.txt` to fetch required packages
3. run re2compiler.py

  to feed regular expression you can use several options:
  1. using cli input (by not providing a file neither specifying `-data`)
  2. using a file
  3. using the `-data` argument
  4. programmatically by recalling compile from another python script as in example.py
  ```
  import re2compiler

  data 	= '(a|b)*'
  output	= re2compiler.compile(data=data)
  print(output)
  ```
  ![screen shot example](https://github.com/DanieleParravicini/re2compiler/blob/master/wiki/howto.PNG)
  
# Optional arguments:
  
| option                     | description                                                                                  | example
|----------------------------|----------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| -h, --help                  | show this help message and exit                                                              |    
| -data [DATA]                | allows to pass the input string representing the regular expression directly via parameter . |
| -dotast DOTAST              | save abstract syntax tree representation using dot format in the given file.                 |![abstract syntax tree example](https://github.com/DanieleParravicini/re2compiler/blob/master/wiki/ast.dot.svg)
| -dotirlowered DOTIRLOWERED  | save ir representation using dot format in the given file.                                   |![ir](https://github.com/DanieleParravicini/re2compiler/blob/master/wiki/ir.dot.svg)
| -dotcode DOTCODE            | save a code representatio using dot format in the given file.                                |![code](https://github.com/DanieleParravicini/re2compiler/blob/master/wiki/code.dot.svg) 
| -o [O]                      | output file containing the code that represent the regular expression.                       |
| -O1                         | perform simple optimization                                                                  |![optimized code](https://github.com/DanieleParravicini/re2compiler/blob/master/wiki/code.dot.optimized.svg)


<a rel="license" href="http://creativecommons.org/licenses/by-nc-nd/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-nd/4.0/88x31.png" /></a><br />This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-nc-nd/4.0/">Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License</a>.
