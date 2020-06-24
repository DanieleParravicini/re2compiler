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
