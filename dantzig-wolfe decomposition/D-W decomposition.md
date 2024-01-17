# Dantzig-Wolfe Decomposition

参考自：
*https://space.bilibili.com/696855224
*运筹优化常用模型、算法及案例实战——Python+Java实现, 刘兴禄，熊望祺，臧永森，段宏达，曾文佳, 清华大学出版社, 2022-10-01

## 基本介绍

### 算法引出

Dantzig-Wolfe分解算法是以George Dantzig和Philp Wolfe的名字命名的。DW分解算法是借助拉格朗日松弛方法，将大量的复杂约束与一个或者多个具有易处理的特殊结构的线性约束分解开。

分解得到的子问题通常具备分块对角结构(block-diagonal)，分块之间相互独立并只包含一部分决策变量。

每个分块对应对应的子问题可能仅仅只是反映了一个组织内部的部分单元、部分时间周期或者其他小规模的模块，它们只是通过一系列的链接约束(linking constraints)与其他子问题联系在一起。

### 算法基本原理

DW分解算法的基本思想是利用子问题具有易处理的结构特点，将一个整体问题分解为一个限制记住问题和一个或者一系列子问题。

(1). RLMP，限制主问题是一个受限制的原问题的近似问题，它通过列生成算法不断扩展，并逐渐提高对原问题的近似程度。

(2). Sub-Problem，子问题负责提供必要的信息，协助主问题逐步提高对原问题的近似程度，并收敛到原问题的最优解。

#### 分解机制

对于这种存在block-diagonal结构的问题，有一种特殊的处理方法，叫做Dantzig-Wolfe分解。

这个方法的基本出发点是把原问题P中的变量进行改写，任何一个变量都可以写成一些定点的集合，然后再用列生成的方法来生成一个个的顶点。

**而变量改写的过程，其实就是把原来的变量用多面体集合的顶点凸组合和极方向锥组合来重写，而需要用到的顶点数量级非常大，这个时候就需要借鉴列生成的思想，虽然有很多顶点，但是可能并不需要这么多顶点。**

DW分解与CG关系非常紧密，两者往往是可以交互的，有点像从不同的角度去看待同一个问题，DW是从顶点的角度，CG是从列的角度。

## 数学模型

$$
\begin{aligned}
 P = \min &  (c^1)^Tx^1 +   & (c^2)^Tx^2 +  & \cdots  + &  (c^k)^Tx^k   &\\
 s.t. &  A^1 x^1 +      & A^2 x^2 +     & \cdots +  &   A^k x^k     &= b  \\
      & D^1 x^1         &               &           &               &\leq d_1 \\
      &                 & D^2 x^2       &           &               &\leq d_2 \\
      &                 &               & \cdots    &               & \\
      &                 &               &           & D^k x^k       & \leq d_k\\
\end{aligned}
$$,


其中，$\sum_{i}A^ix^i = b$为难处理的约束，也称之为耦合约束，而剩下约束称之为容易处理的约束。


假设我们去掉第一个约束，那么该问题P剩下的约束条件，每个子系统需要完成的决策$x$其实是相互独立的，而且目标函数也是k个子系统的线性组合，在这种情况下，这个问题是可以被分解的，分解成k个min问题，每个min问题对一个子系统求解。

子问题往往是容易处理的，约束条件可以当做是背包约束，再加上一个线性目标函数，可以当做背包问题来求解，使用动态规划算法。


### 拉格朗日松弛

按照上述章节描述，第一个约束是个难处理的约束，因为这个约束的存在，$x^1, \cdots, x^k$等不能互相独立。如果我们对第一个约束做拉格朗日松弛，整理后，原问题被松弛为一个个子系统的线性组合，那么获得原问题P的拉个朗日松弛问题LD(P)问题。

$$
\begin{aligned}
 LD(P) = \min & \sum_{k=1}^{K} ((c^k)^T-\lambda^TA^k)x^k &&+ \lambda^T b&& \\
 s.t. & D^1 x^1         &               &           &               &\leq d_1 \\
      &                 & D^2 x^2       &           &               &\leq d_2 \\
      &                 &               & \cdots    &               & \\
      &                 &               &           & D^k x^k       & \leq d_k\\
      &    x^1\in Z_{+}^{n_1}            &      \cdots         &           &   x^k\in Z_{+}^{n_k}      & \\
\end{aligned}
$$,

### LD(P)问题的等价变换

LD(P)问题可以表示为：

$$
\begin{aligned}
 LD(P) = \min & \sum_{k=1}^{K} (c^k)^Tx^k &  \\
 s.t. & \sum_{k=1}^{K} (A^k)^Tx^k & = b \\
       &  x^k \in X^k=\{x^k \in Z^{n_k}| D^kx^k \leq d_k \}
\end{aligned}
$$,


### IPM问题的引出

假设$X^k$是一个有界的多面体，$X^k$中的任一点都可以写成顶点的凸组合(假设所有顶点都是已知的)。

假设我们可以找到所有$x^k$通过可行域的顶点的凸组合，那么对LP(D)进行改写，模型如下：

$$
\begin{aligned}
 IPM = \min & \sum_{k=1}^{K} (c^k)^T \sum_{t=1}^{T_k} \lambda_{kt}x^{kt}  &  \\
 s.t. & \sum_{k=1}^{K} (A^k)^T \sum_{t=1}^{T_k} \lambda_{kt}x^{kt} & = b \\
       & \sum_{t=1}^{T_k} \lambda_{kt}x^{kt} = 1 \\
       & \lambda_{kt} \in \{0, 1\}, \forall k, t  \\
\end{aligned}
$$,

这个替换后的问题叫做IPM问题，也就是IP master problems， IP主问题。

**在这个IPM中，假设所有的$x^{kt}$都是已知的，要么是多面体的所有顶点，要么是整数集合中的所有整数元素。**

*注意这里的IPM与P是完全等价的，只是变量换了形式，原来是整数规划问题，现在是0-1变量问题。*


## 模型分解

### 块角模型

考虑下面的线性规划问题：

$$
\begin{aligned}
 \min &  & c^Tx  \\
 s.t. & & Ax \leq b \\
      & & x \in R^n \\
\end{aligned}
$$,

其中约束矩阵A有以下特定结构：



$$
Ax = \left[
\begin{matrix}
B_0 & B_1 & B_2 & \cdots & B_K \\
 & A_1 &   &   &   \\
  &   & A_2 &   &   \\
  &   &   & \ddots &  \\
  &   &   & &   A_K \\
\end{matrix}
\right]
\left[
\begin{matrix}
x_0  \\
x_1  \\
x_2  \\
\vdots  \\
x_4  \\
\end{matrix}
\right]=\left[
\begin{matrix}
b_0  \\
b_1  \\
b_2  \\
\vdots  \\
b_K  \\
\end{matrix}
\right]
$$

其中，约束矩阵中的第一行，称之为链接约束，我们也称之为难约束(hard constraint)。

D-W分解算法的思想就是将上述模型进行分解，而不是考虑所有约束一起求解，将问题分解为主题和若干子问题进行求解，主问题考虑链接约束，子问题进行分开求解，从而只有一系列更小规模的问题需要我们求解。

### Minkowski表示定理

参考自：
Kalvelagen, Erwin. "Two-stage stochastic linear programming with GAMS." GAMS Corporation (2003).

考虑线性规划问题的可行域：

$$
\begin{aligned}
P = \{x|Ax=b, x \geq 0\}
\end{aligned}\tag{1}
$$
如果$P$是有界的，那么可以将点$x\in P$表示成$P$的极点$x^{(j)}$的线性组合形式，如下：
$$
\begin{aligned}
x = \sum_{j} \lambda_j x^{(j)} \\
\sum_{j} \lambda_j  = 1 \\
\lambda_j \geq 0
\end{aligned}\tag{2}
$$
如果$P$是不是有界的情况，那么需要引入极射线，如下：
$$
\begin{aligned}
x = \sum_{j} \lambda_j x^{(j)} + \sum_{i} \mu_i r^{(i)} \\
\sum_{j} \lambda_j  = 1 \\
\lambda_j \geq 0 \\
\mu_i \geq 0
\end{aligned}\tag{3} 
$$

其中式子$r^{(i)}$是$P$的极射线，上述表述被称作Minkowski表示定理，约束$\sum_{j} \lambda_j =1$即上文提到的凸约束。

也可以使用如下的更加一般的表达式：

$$
\begin{aligned}
x = \sum_{j} \lambda_j x^{(j)}  \\
\sum_{j} \delta_j \lambda_j  = 1 \\
\lambda_j \geq 0 \\
\mu_i \geq 0
\end{aligned}\tag{4} 
$$
其中，
$$
\begin{aligned}
\delta_j  = \left\{ 
        \begin{array}{ll} 
        1, & x^{(j)} 是一个极点  \\ 
        0, & x^{(j)} 是一个极射线
        \end{array} 
        \right.
\end{aligned}
$$

通过上述形式，就可以把原问题关于变量$x$的形式转换为关于变量$\lambda$的形式，当然，随着变量$\lambda_j$的数量增多，该模型逐渐变得不能直接使用商业求解器求解。

### 补充知识

上述提到的极点与极射线是凸分析和线性规划领域的一个重要概念，尤其是在处理无界可行域时，我们需要厘清这些概念的含义及其之间的关系：

1). 极点（Extreme Points）：在凸集中，极点是不能表示为其他两个不同点的凸组合的点。在很多情况下，极点是定义凸集形状的关键点。

2). 极射线（Extreme Rays）/极方向（Extreme Directions）：对于一个无界的凸集，极射线是指从凸集内的一点出发，沿着某个方向无限延伸的射线，这个射线完全位于凸集内部。在无界可行域的情况下，极射线代表着可行解可以无限远地延伸的方向。

3). 凸组合和锥组合：凸组合是指系数和为1的线性组合，而锥组合则是系数为非负的线性组合。

凸组合（Convex Combination）:

定义：在向量空间中，如果有一组向量 $v_1, v_2, \cdots, v_i$ 和一组非负实数 $\lambda_1, \lambda_2, \cdots, \lambda_i$，且满足 $\sum_{i} \lambda_i  = 1, \lambda_i \geq 0 $，那么这些向量的线性组合被称为它们的凸组合。

特点：凸组合的关键在于系数之和必须等于1，并且每个系数都是非负的。这意味着凸组合产生的新向量位于原始向量形成的凸集内。

锥组合（Conic Combination）:

定义：在向量空间中，如果有一组向量 $v_1, v_2, \cdots, v_i$ 和一组非负实数 $\lambda_1, \lambda_2, \cdots, \lambda_i$，且满足 $\lambda_i \geq 0$，那么这些向量的线性组合被称为它们的锥组合。
​

特点：锥组合与凸组合的主要区别在于，锥组合的系数之和不一定等于1，但系数依然需要是非负的。锥组合形成的结构是一个锥形，而不是凸集。

区别:
1. 凸组合的核心在于系数之和必须等于1，而锥组合没有这个要求。
2. 凸组合产生的结果总是位于原始向量形成的凸集内部或边界上，而锥组合形成的是一个无限延伸的锥形。
3. 凸组合用于表达介于原始向量之间的点，而锥组合用于表达原始向量形成的锥形空间内的所有点。

### 模型分解

下面将模型分解成主问题和K个子问题，K个子问题有如下约束形式：

$$
\begin{aligned}
A_k x_k = b_k \\
x_k \geq 0
\end{aligned} 
$$

主问题如下：

$$
\begin{aligned}
 \min &  & c_k^Tx_k  \\
 s.t. & & B_kx_k = b_0 \\
      & & x_0 \geq 0 \\
\end{aligned}
$$,

我们将极点与极射线式代入到上述的主问题，得到

$$
\begin{aligned}
 \min &  & c_0^Tx_0 + \sum_{k=1}^{K}\sum_{j=1}^{p_k} (c_k^Tx_k^{(j)}) \lambda_{k,j} \\
 s.t. & & B_0x_0 + \sum_{k=1}^{K}\sum_{j=1}^{p_k} (B_kx_k^{(j)}) \lambda_{k,j}  = b_0 \\
      & & \sum_{j=1}^{p_k} \delta_{k,j} \lambda_{k,j}  = 1, \forall k \in 1, 2, \cdots, K \\
      & & x_0 \geq 0 \\
      & & \lambda_{k,j} \geq 0
\end{aligned}
$$,

这其中，$p_k$是第$k$个子问题的极点个数，这个线性规划问题的变量很多(注意，该问题的变量已经为$\lambda_{k,j}$)，所以直接求解仍然不切实际，借鉴列生成的思想，只考虑那些检验数有希望为负数的变量。$x_0$为决策变量的第一个，在这里，我们可以假定通过其它启发式算法或者规则获得它的值。

由此得到限制性主问题(Restricted Master Problem)，模型如下：
$$
\begin{aligned}
 \min &  & c_0^Tx_0 + c^T \lambda' \\
 s.t. & & B_0x_0 + B\lambda'  = b_0 \\
      & & \Delta\lambda' = 1 \\
      & & x_0 \geq 0 \\
      & & \lambda_{k,j} \geq 0
\end{aligned}
$$ 
限制主问题的列是不固定的，随着列生成，会有新的列加入该模型中，评价变量$\lambda_{k,j}$是否可以被加入到主问题模型中的规则为其检验数（reduced cost），将链接约束$B_0x_0 + B\lambda'  = b_0$对应的对偶变量记为$\pi_1$，把凸约束$\sum_{j=1}^{p_k} \delta_{k,j} \lambda_{k,j}  = 1, \forall k \in K$的对偶变量记作$\pi^k_2$，则主问题中变量$\lambda'_{k,j}$的检验数可以写作

$$
\sigma_{k,j} = (c_k^Tx_k^{(j)}) - \pi^T
\left(
\begin{matrix}
B_k x_k^{(j)} \\
\delta_{k,j} \\
\end{matrix}
\right) = (c^T_k - \pi^T_1 B_k)x_k^{(j)} -\pi^T_2 \delta_{k,j}
$$

如果子问题是有界的，那么通过检验数评价后，最有希望改进主问题的基本可行解$x_k$可以通过求解下面以检验数为目标函数的模型得到：

$$
\begin{aligned}
 \min_{x_k} &  & \sigma_k = (c^T_k - \pi^T_1 B_k)x_k -\pi^T_2 \\
 s.t. &  &A_k x_k = b_k \\
&  &x_k \geq 0
\end{aligned}
$$ 

寻找这些检验数的过程叫做pricing，如果$\sigma_k \leq 0$，就可以将新列$\lambda_{k,j}$加入主问题中，该列的成本系数为$c_k^T x_k^*$(注意该成本系数为原主问题的成本系数)。

## 算例

$$
\begin{aligned}
 \max & & z = 90x_1& +80x_2& +70x_3& +60x_4 &  \\
s.t.  & & 3x_1 & + x_2 &  & &\leq 12  \\
      & & 2x_1 & + x_2 & & &\leq 10  \\
      & &  & &3x_3 & + 2x_4 &\leq 15  \\
      & &  & &x_3 & + x_4 &\leq 4 \\
      & &  x_1&, x_2 &,x_3 & , x_4 & \geq 0
\end{aligned}
$$ 