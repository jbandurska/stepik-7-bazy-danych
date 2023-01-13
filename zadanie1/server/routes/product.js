const express = require("express");
const productRoutes = express.Router();
const dbo = require("../db/conn");
const ObjectId = require("mongodb").ObjectId;

productRoutes.route("/product").get(function (req, res) {
  let db_connect = dbo.getDb("store");
  let filter = req.body.filter
    ? { [req.body.filter.kategoria]: new RegExp(req.body.filter.klucz, "i") }
    : {};
  let sort = req.body.sort
    ? { [req.body.sort.kategoria]: req.body.sort.kolejnosc }
    : {};

  db_connect
    .collection("products")
    .find(filter)
    .sort(sort)
    .toArray(function (err, result) {
      if (err) throw err;
      res.json(result);
    });
});

productRoutes.route("/product/:id").get(function (req, res) {
  let db_connect = dbo.getDb("store");
  let myquery = { _id: ObjectId(req.params.id) };
  db_connect.collection("products").findOne(myquery, function (err, result) {
    if (err) throw err;
    res.json(result);
  });
});

productRoutes.route("/product/add").post(function (req, response) {
  let db_connect = dbo.getDb("store");
  db_connect
    .collection("products")
    .findOne({ nazwa: req.body.nazwa }, function (err, res) {
      if (res == null) {
        let myobj = {
          nazwa: req.body.nazwa,
          cena: req.body.cena,
          opis: req.body.opis,
          ilosc: req.body.ilosc,
        };
        db_connect.collection("products").insertOne(myobj, function (err, res) {
          if (err) throw err;
          response.json(res);
        });
      } else {
        response.json({ message: "Produkt z taką nazwą już istnieje" });
      }
    });
});

productRoutes.route("/product/:id").put(function (req, response) {
  let db_connect = dbo.getDb("store");
  let myquery = { _id: ObjectId(req.params.id) };
  let newValues = {
    $set: req.body,
  };
  db_connect
    .collection("products")
    .updateOne(myquery, newValues, function (err, res) {
      if (err) throw err;
      console.log("1 document updated successfully");
      response.json(res);
    });
});

productRoutes.route("/product/:id").delete(function (req, res) {
  let db_connect = dbo.getDb("store");
  let myquery = { _id: ObjectId(req.params.id) };
  db_connect.collection("products").deleteOne(myquery, function (err, obj) {
    if (err) throw err;
    console.log("1 document deleted");
    if (obj.deletedCount === 0)
      res.status(404).json({ błąd: "Obiekt o takim id nie istnieje." });
    else res.json(obj);
  });
});

productRoutes.route("/product/generate/report").get(function (req, res) {
  let db_connect = dbo.getDb("store");
  db_connect
    .collection("products")
    .aggregate([
      {
        $project: {
          nazwa: 1,
          wartosc: { $multiply: ["$cena", "$ilosc"] },
        },
      },
    ])
    .toArray(function (err, obj) {
      if (err) throw err;
      res.json(obj);
    });
});

module.exports = productRoutes;
