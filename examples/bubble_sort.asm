; Easy Bubble Sort - 8086 (sorts 20 numbers, smallest first)
; Numbers are stored in memory from address 0500h (1280 in decimal)

start:
MOV SI, 1280            ; SI points to the first number

; ---- put the 20 numbers in memory ----
MOV word [SI], 4500
MOV word [SI+2], 123
MOV word [SI+4], 65000
MOV word [SI+6], 872
MOV word [SI+8], 15
MOV word [SI+10], 40000
MOV word [SI+12], 3
MOV word [SI+14], 999
MOV word [SI+16], 32768
MOV word [SI+18], 1500
MOV word [SI+20], 77
MOV word [SI+22], 2048
MOV word [SI+24], 60000
MOV word [SI+26], 250
MOV word [SI+28], 18
MOV word [SI+30], 12345
MOV word [SI+32], 500
MOV word [SI+34], 31000
MOV word [SI+36], 9
MOV word [SI+38], 256

; ---- sort ----
MOV DX, 19              ; do 19 rounds

round:
MOV SI, 1280            ; start from the first number
MOV CX, 19              ; compare 19 pairs in each round

compare:
MOV AX, word [SI]       ; AX = left number
MOV BX, word [SI+2]     ; BX = right number
CMP AX, BX              ; compare them
JBE skip                ; if left <= right, do nothing
MOV word [SI], BX       ; else swap
MOV word [SI+2], AX

skip:
ADD SI, 2               ; go to next pair
DEC CX
JNZ compare             ; repeat for all 19 pairs

DEC DX
JNZ round               ; repeat for all 19 rounds
HLT                     ; stop
