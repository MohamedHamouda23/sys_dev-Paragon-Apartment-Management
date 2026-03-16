from database.databaseConnection import check_connection


def get_tenant_payments(user_id):
	"""Return payment rows for the tenant linked to the given user_id."""
	conn = check_connection()
	if conn is None:
		return []

	cursor = conn.cursor()
	cursor.execute(
		"""
		SELECT
			p.payment_id,
			l.lease_id,
			b.street || ' (' || b.postcode || ')' AS apartment,
			p.due_date,
			COALESCE(p.payment_date, '-') AS payment_date,
			p.amount,
			CASE
				WHEN p.payment_date IS NULL THEN 'Pending'
				ELSE 'Paid'
			END AS status,
			CASE
				WHEN p.Is_late = 1 THEN 'Yes'
				ELSE 'No'
			END AS is_late
		FROM Payment p
		JOIN Lease l ON p.lease_id = l.lease_id
		JOIN Apartments a ON l.apartment_id = a.apartment_id
		JOIN Buildings b ON a.building_id = b.building_id
		JOIN Tenant t ON l.tenant_id = t.tenant_id
		WHERE t.user_id = ?
		ORDER BY p.due_date ASC
		""",
		(user_id,),
	)
	rows = cursor.fetchall()
	conn.close()
	return rows
