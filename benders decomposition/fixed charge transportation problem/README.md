# 说明
在这个例子中，我们对下面这个例子使用了benders decomposition方法。

An example of Benders Decomposition on fixed charge transportation
problem bk4x3.
Optimal objective in reference : 350.
Erwin Kalvelagen, December 2002
See:
http://www.in.tu-clausthal.de/~gottlieb/benchmarks/fctp/

其中，FCTP master problem直接建模求解。

FCTP benders decomposition使用benders方法求解

# 1. Benders cut 

给定
$$\hat{y} = [0,0,0,0,0,0,0,0,0,0,0,0]$$
，每次迭代后的$y$值与cut分别为：

第0次，
$$y = [0,0,0,0,0,0,0,0,0,0,0,0]$$
feasibility cut,

$100.0 -10.0*y_0_0 -10.0*y_0_1 -10.0*y_0_2 -20.0*y_1_0 -30.0*y_1_1 -30.0*y_1_2 -20.0*y_2_0 -40.0*y_2_1 -30.0*y_2_2 -20.0*y_3_0 -20.0*y_3_1 -20.0*y_3_2 <= 0$

<br>

第1次，
$$y = [1,1,1,1,1,1,1,1,1,1,1,1]$$
optimality cut,

$250.0 -10.0*y_1_2 -20.0*y_4_3 <= q$