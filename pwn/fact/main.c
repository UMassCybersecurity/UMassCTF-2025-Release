#include <stdlib.h>
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>

char *change_name(char *name) {
    printf("Please type in your new name:\n");
    scanf("%8s", name);
    printf("Your current name is: %s\n", name);
    return name;
}

char *rename_(char *name) {
    char id[8];
    for (int i = 0; i < 7; i++) {
        id[i] = rand() % 26 + 'a';
    }
    id[7] = 0;
    printf("Changing your name? How about %s?\n", id);
    return change_name(name);
}

char *first_time_name() {
    char id[32];
    for (int i = 0; i < 32; i++) {
        id[i] = rand() % 26 + 'a';
    }
    id[31] = 0;
    printf("Welcome to session %s!\n", id);
    char str[8];
    return change_name(str);
}

void multiplication_facts(unsigned long long int a, unsigned long long int b, char *name) {
    printf("%s, did you know that %llu * %llu = %llu?\n", name, a, b, a * b);
}

void square_root_facts(unsigned long long int a, char *name) {
    printf("%s, did you know that the square root of %llu is %llu?\n", name, a * a, a);
}

void xor_facts(unsigned long long int a, unsigned long long int b, char *name) {
    printf("%s, did you know that the bitwise XOR of %llu and %llu is %llu\n", name, a, b, a ^ b);
}

void math_facts(char *name) {
    short operations = rand() % 3;
    unsigned long long int a = rand();
    unsigned long long int b = rand();
    switch (operations) {
        case 0:
            square_root_facts(a, name);
            break;
        case 1:
            multiplication_facts(a, b, name);
            break;
        case 2:
            xor_facts(a, b, name);
            break;
        default:
            printf("Hmmmmm, no math facts for you, %s\n", name);
    }
}


int main() {
    setbuf(stdout, NULL);
    srand(time(NULL));
    char *name = first_time_name();
    char i[1];
    while (1) {
        printf("Options:\na. Rename\nb. Do math!\nc. Exit\n");
        scanf("%1s", i);
        if (i[0] == 'a') {
            rename_(name);
        } else if (i[0] == 'b') {
            math_facts(name);
        } else {
            break;
        }
    }
}

void win() {
    int fd = open("flag.txt", O_RDONLY);
    char s[128] = {0};
    read(fd, s, 128);
    printf("%s\n", s);
    exit(0);
}