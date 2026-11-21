#include<stdio.h>
#include<math.h>

void swap(int *a , int *b) ;

int main(void) {
	int first , *a = &first ;
	int second , *b = &second ;
	scanf("%d %d" , &first , &second) ;
	swap(a , b) ;
	printf("%d %d" , *a , *b) ;
	return 0 ;
}

void swap(int *a , int *b) {
	int temp ; 
	temp = *a ;
	*a = *b ;
	*b = temp ;
}
