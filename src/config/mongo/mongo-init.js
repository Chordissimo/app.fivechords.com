db.createUser(
        {
            user: "aichords",
            pwd: "12345",
            roles: [
                {
                    role: "readWrite",
                    db: "aichords"
                }
            ]
        }
);
db.aichords.insertOne(
  { "init_db": "ok" }
);
