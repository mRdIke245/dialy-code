#include<stdio.h>
#include<math.h>

int main(void){
	double input ;
	scanf("%lf" , &input) ;
	double yingshui , yingjiao ;
	if(input < 5000) {
		yingshui = 0.00 ;
		yingjiao = 0.00 ;
	}
	else {
		yingshui = input - 5000  ;
		if(yingshui < 5000) {
			yingjiao = yingshui * 0.03 ;
		}
		else if(yingshui > 5000 && yingshui < 20000) {
			yingjiao = yingshui * 0.1 ;
		}
		else if(yingshui > 20000 && yingshui < 50000) {
			yingjiao = yingshui * 0.2 ;
		}
		else if(yingshui > 50000 && yingshui < 100000) {
			yingjiao = yingshui * 0.25 ;
		}
		else if(yingshui > 100000) {
			yingjiao = yingshui * 0.3 ;
		}
	}
	printf("%.2f %.2f", yingshui , yingjiao );
	return 0 ;
}
