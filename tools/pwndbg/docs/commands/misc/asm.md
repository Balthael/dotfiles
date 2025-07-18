<!-- THIS PART OF THIS FILE IS AUTOGENERATED. DO NOT MODIFY IT. See scripts/generate_docs.sh -->




# asm

## Description


Assemble shellcode into bytes
## Usage


```bash
usage: asm [-h] [-f {hex,string}]
           [--arch {powerpc64,aarch64,powerpc,riscv32,riscv64,sparc64,mips64,msp430,alpha,amd64,sparc,thumb,cris,i386,ia64,m68k,mips,s390,none,avr,arm,vax}]
           [-v AVOID] [-n] [-z] [-i INFILE]
           [shellcode ...]

```
## Positional Arguments

|Positional Argument|Help|
| :--- | :--- |
|shellcode|Assembler code to assemble (default: '[]')|

## Optional Arguments

|Short|Long|Help|
| :--- | :--- | :--- |
|-h|--help|show this help message and exit|
|-f|--format|Output format (default: 'hex')|
||--arch|Target architecture|
|-v|--avoid|Encode the shellcode to avoid the listed bytes (provided as hex)|
|-n|--newline|Encode the shellcode to avoid newlines|
|-z|--zero|Encode the shellcode to avoid NULL bytes|
|-i|--infile|Specify input file|

<!-- END OF AUTOGENERATED PART. Do not modify this line or the line below, they mark the end of the auto-generated part of the file. If you want to extend the documentation in a way which cannot easily be done by adding to the command help description, write below the following line. -->
<!-- ------------\>8---- ----\>8---- ----\>8------------ -->
