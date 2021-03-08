#include <stdio.h>
#include <stdlib.h>
int BITS_INSTR_TYPE = 16-3;

int main(){
    FILE* fp= fopen("a.out","r");
    int pc=0;
    while( !feof(fp)){
        int i;
        fscanf(fp,"%x",&i);
        printf("%03d: %x \\\\ ", pc, i);
        int type=i>>(BITS_INSTR_TYPE);
        int data= i%(1<< (BITS_INSTR_TYPE));
        switch (type)
        {
        case 0:
            printf("ACCEPT\n");
            /* code */
            break;
        case 1:
            printf("SPLIT\t {%d,%d} \n", pc+1, data);
            /* code */
            break;
        case 2:
            printf("MATCH\t char %c\n", data);
            /* code */
            break;
        case 3:
            printf("JMP to \t %d \n", data);
            /* code */
            break;
        case 4:
            printf("END_WITHOUT_ACCEPTING\n");
            /* code */
            break;
        case 5:
            printf("MATCH_ANY\n");
            /* code */
            break;
        case 6:
            printf("ACCEPT_PARTIAL\n");
            /* code */
            break;
        case 7:
            printf("NOT_MATCH\t char %c\n", data);
            /* code */
            break;
        default:
            printf("UNKNOWN %d\t data %d\n",type, data);
            break;
        }
        
        pc+=1;
        fscanf(fp,"\n");
    }
}