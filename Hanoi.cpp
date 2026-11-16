#include<stdio.h>
#include<math.h>

void move(int n , char a , char b) ;

void hanoi(int n , char X , char Y , char Z) ;

int main(void) {
	int n ; 
	scanf("%d" , &n) ;
	hanoi(n , 'X' , 'Y' , 'Z') ;
	return 0 ;
}
void hanoi(int n , char X , char Y , char Z) {
	if(1==n) {
		move(n , X , Z) ;
	}
	else {
		hanoi(n-1 , X , Z , Y) ;
		move(n , X , Z) ;
		hanoi(n-1 , Y , X , Z) ;
	}
}
void move(int n , char A , char B) {
	printf("%d : %c -> %c\n" , n , A , B) ;
}
