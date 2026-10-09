# 0004 - Vial temperature entering the hazard is the interval mean

Found by a property test: sampling the vial temperature at the start of each interval lags the air by one step even as tau -> 0.
The implementation integrates the hazard over the exact interval-mean vial temperature (`exponential_integrator(..., output="mean")`), which tends to the air temperature as tau -> 0.
Point values (`output="edge"`) are kept for verification against the analytic step response (E3). Jensen's inequality (convex Arrhenius rate within an interval) is a second-order effect not modelled; refine dt if it matters.
