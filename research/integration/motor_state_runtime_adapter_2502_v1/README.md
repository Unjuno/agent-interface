# Pure MotorState runtime adapter (#2502)

This module promotes the scoped #2490 mapping into a reusable pure function.
It is intentionally not a backend adapter: no GUI imports, input dispatch,
lease mutation, authority extension, or application-effect inference.
