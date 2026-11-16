; Fibonacci Series - first 15 numbers stored from address 0500h
start:
MOV SI, 1280
MOV AX, 0
MOV BX, 1
MOV CX, 15
next:
MOV word [SI], AX
ADD SI, 2
MOV DX, BX
ADD BX, AX
MOV AX, DX
DEC CX
JNZ next
HLT
