	function [x y z] = get_satellite_position(eph, t, compute_harmonic_correction)
	% get_satellite_position: computes the position of a satellite at time (t) given the
	% ephemeris parameters.
	% Usage: [x y z] =  get_satellite_position(eph, t, compute_harmonic_correction)
	% Input Args: eph: ephemeris data
	%             t: time
	%             compute_harmonic_correction (optional): 1 if harmonic
	%             correction should be applied, 0 if not.
	% Output Args: [x y z] in ECEF in meters
	% ephmeris data must have the following fields:
	% rcvr_tow (receiver tow)
	% svid (satellite id)
	% toc (reference time of clock parameters)
	% toe (referece time of ephemeris parameters)
	% af0, af1, af2: clock correction coefficients
	% ura (user range accuracy)
	% e (eccentricity)
	% sqrtA (sqrt of semi-major axis)
	% dn (mean motion correction)
	% m0 (mean anomaly at reference time)
	% w (argument of perigee)
	% omg0 (lontitude of ascending node)
	% i0 (inclination angle at reference time)
	% odot (rate of right ascension)
	% idot (rate of inclination angle)
	% cus (argument of latitude correction, sine)
	% cuc (argument of latitude correction, cosine)
	% cis (inclination correction, sine)
	% cic (inclination correction, cosine)
	% crs (radius correction, sine)
	% crc (radius correction, cosine)
	% iod (issue of data number)


	% set default value for harmonic correction
	switch nargin
		case 2
			compute_harmonic_correction=1;
	end
	mu = 3.986005e14;
	omega_dot_earth = 7.2921151467e-5; %(rad/sec)

	% Now follow table 20-IV
	A = eph.sqrtA^2;
	cmm = sqrt(mu/A^3); % computed mean motion
	tk = t - eph.toe;
	% account for beginning of end of week crossover
	if (tk > 302400)
		tk = tk-604800;
	end
	if (tk < -302400)
		tk = tk+604800;
	end
	% apply mean motion correction
	n = cmm + eph.dn;

	% Mean anomaly
	mk = eph.m0 + n*tk;

	% solve for eccentric anomaly
	syms E;
	eqn = E - eph.e*sin(E) == mk;
	solx = vpasolve(eqn, E);
	Ek = double(solx);

	% True anomaly:
	nu = atan2((sqrt(1-eph.e^2))*sin(Ek)/(1-eph.e*cos(Ek)), (cos(Ek)-eph.e)/(1-eph.e*cos(Ek)));
	%Ek = acos((e  + cos(nu))/(1+e*cos(nu)));

	Phi = nu + eph.w;
	du = 0;
	dr = 0;
	di = 0;
	if (compute_harmonic_correction == 1)
	% compute harmonic corrections
	du = eph.cus*sin(2*Phi) + eph.cuc*cos(2*Phi);
	dr = eph.crs*sin(2*Phi) + eph.crc*cos(2*Phi);
	di = eph.cis*sin(2*Phi) + eph.cic*cos(2*Phi);
	end

	u = Phi + du;
	r = A*(1-eph.e*cos(Ek)) + dr;

	% inclination angle at reference time
	i = eph.i0 + eph.idot*tk + di;
	x_prime = r*cos(u);
	y_prime = r*sin(u);
	omega = eph.omg0 + (eph.odot - omega_dot_earth)*tk - omega_dot_earth*eph.toe;

	x = x_prime*cos(omega) - y_prime*cos(i)*sin(omega);
	y = x_prime*sin(omega) + y_prime*cos(i)*cos(omega);
	z = y_prime*sin(i);

	end
