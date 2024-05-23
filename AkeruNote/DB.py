DB_type = "plaintext"#"plaintext" or "mondoDB"


if DB_type == "plaintext":
	from Akeru.HatenaDB import Database
elif DB_type == "mondoDB":#not yet implemented
	from Akeru.HatenaDB import Database#hue
else:
	import sys
	print("Unsupported database type \"%s\"" % DB_type)
	sys.exit()