#include<stdio.h>
int main(void) {
	int n;
	scanf("%d",&n);
	char arr[n];
	getchar();
	for(int i=0;i<n;i++) {
		scanf("%c",&arr[i]);
	}
	for(int i=0;i<n;i++) {
		arr[i] = arr[i]+2;
	}
	for(int i=0;i<n;i++) {
		printf("%c",arr[i]);
	}
	return 0;
}
