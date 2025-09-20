# algorithm_map.py
ALGORITHM_MAP = {
    "root_finding": ["Bisection","Regula Falsi","Secant","Newton-Raphson","Brentq","Fixed-point","Muller"],
    "linear_system": ["Gaussian Elimination","LU","Cholesky","Jacobi","Gauss-Seidel","SOR","Conjugate Gradient","GMRES"],
    "integration": ["Trapezoid","Simpson","Romberg","Adaptive Quadrature","Gaussian Quadrature","Monte Carlo"],
    "differentiation": ["Forward Diff","Central Diff","Richardson"],
    "ode_ivp": ["Euler","RK4","RK45","Implicit Euler","BDF"],
    "ode_bvp": ["Shooting","Finite Difference","Collocation"],
    "pde": ["Finite Difference","Finite Element","Spectral Method","Finite Volume"],
    "optimization_unconstrained": ["Gradient Descent","Newton","BFGS","Conjugate Gradient","Nelder-Mead"],
    "optimization_constrained": ["Lagrange","SQP","Interior Point","Augmented Lagrangian"],
    "approximation": ["Polynomial Interpolation","Spline","Chebyshev","Least Squares"],
    "eigen": ["Power Method","Inverse Power","QR","Lanczos","Arnoldi"],
    "stochastic": ["Monte Carlo","MCMC","Importance Sampling"]
}