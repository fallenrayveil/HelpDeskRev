const express = require('express');
const bodyParser = require('body-parser');
const authRoutes = require('./routes/authRoutes');
// const hdeskRoutes = require('./routes/hdeskRoutes');
const PORT = process.env.PORT || 3000;

const app = express();

app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.json());

app.use('/auth', authRoutes);
// app.use('/hdesk', hdeskRoutes);

app.listen(PORT, () => {
    console.log(`Server berjalan di http://localhost:${PORT}`);
});
