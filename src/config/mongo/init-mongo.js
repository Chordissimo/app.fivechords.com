db.createUser(
    {
        user: "aichords",
        pwd: "12345",
        roles:[
            {
                role: "readWrite",
                db:   "mydatabase"
            }
        ]
    }
);
db.aichords.insertOne(
  { "init_db": "ok" }
);
