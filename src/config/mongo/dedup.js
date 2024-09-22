db.RECOGNITIONS.aggregate([
  { $sort: { video_id: 1, _id: -1 } }, 
  { $group: { _id: "$video_id", dups: { $push: "$_id" }, count: { $sum: 1 } } },
  { $match: { count: { $gt: 1 } } }
], { allowDiskUse: true }).forEach(function (doc) {
  doc.dups.shift();
  db.RECOGNITIONS.remove({ _id: { $in: doc.dups } })
});
