#include<stdio.h>
#include<math.h>

int factorial(int n);
int main(void)
{
	int n;
	scanf("%d",&n);
	double result=0.0;
	for(int i=n;i>0;i--) {
		double middle=1/factorial(i);
		result+=middle;
	}
	printf("%f",result);
	return 0;
}
int factorial(int n) {
	int f=0;
	if(0==n){
		f=1;
	}
	else {
		f=n*factorial(n-1);
	}
	return f;
}
