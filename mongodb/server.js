const { MongoClient, ObjectId } = require('mongodb');
const express = require('express');

const app = express();

const mongoUrl = 'mongodb://localhost:27017';
const dbName = 'products';
const collectionName = 'products';

app.use(express.json());

app.get('/products', async (req, res) => {
    try {
        console.log("Retrieving all products");
        const client = await MongoClient.connect(mongoUrl, { useNewUrlParser: true });
        const collection = client.db(dbName).collection(collectionName);
        
        let filter = {};
        if (req.query.name) {
            filter.name = new RegExp(req.query.name, 'i');
        }
        if (req.query.price) {
            filter.price = parseInt(req.query.price);
        }
        if (req.query.quantity) {
            filter.quantity = parseInt(req.query.quantity);
        }
        
        let sort = {};
        if (req.query.sort) {
            sort = JSON.parse(req.query.sort);
        }
        const products = await collection.find(filter).sort(sort).toArray();
        
        res.json(products);
    } catch (err) {
        res.status(500).json({ message: err.message });
    }
});

app.post('/products', async (req, res) => {
    try {
        console.log("Creating new product");
        const client = await MongoClient.connect(mongoUrl, { useNewUrlParser: true });
        const collection = client.db(dbName).collection(collectionName);
        
        const existingProduct = await collection.findOne({ name: req.body.name });
        if (existingProduct) {
            res.status(400).json({ message: 'Product name not unique.' });
        } else {
            const result = await collection.insertOne(req.body);
            client.close();
            res.json(result);
        }
    } catch (err) {
        res.status(500).json({ message: err.message });
    }
});

app.put('/products/:id', async (req, res) => {
    try {
        console.log("Updating product with id: " + req.params.id);
        const client = await MongoClient.connect(mongoUrl, { useNewUrlParser: true });
        const collection = client.db(dbName).collection(collectionName);
        
        const result = await collection.updateOne({ _id: ObjectId(req.params.id) }, { $set: req.body });
        client.close();
        res.json(result);
    } catch (err) {
        res.status(500).json({ message: err.message });
    }
});

app.delete('/products/:id', async (req, res) => {
    try {
        console.log("Deleting product with id: " + req.params.id);
        const client = await MongoClient.connect(mongoUrl, { useNewUrlParser: true });
        const collection = client.db(dbName).collection(collectionName);
        const result = await collection.deleteOne({ _id: ObjectId(req.params.id) });
        if(result.deletedCount === 0){
            res.status(404).json({ message: 'Product not found or unable to delete' });
        }
        client.close();
        res.json(result);
    } catch (err) {
        res.status(500).json({ message: err.message });
    }
    


  });

  app.get('/products/report', async (req, res) => {
  try {
  console.log("Retrieving product report");
  const client = await MongoClient.connect(mongoUrl, { useNewUrlParser: true });
  const collection = client.db(dbName).collection(collectionName);
  const report = await collection.aggregate([
    {
        $group: {
            _id: null,
            totalQuantity: { $sum: '$quantity' },
            totalValue: { $sum: { $multiply: ['$quantity', '$price'] } }
        }
    }, 
    {
        $project: {
            _id: 0
        }
    }
]).toArray();

res.json(report);
} catch (err) {
res.status(500).json({ message: err.message });
}
});


app.listen(5000);
console.log("App listening at port 5000");