prep = {
    "src":["from", "out", "out_of", "off", "off_of"],
    "dest_conf": ["into", "onto"],
    "dest_dir": ["for", "at", "to", "towards"],
    "dir":[
        "across", "along", "around", "down", "over", "past", "round",
        "through", "towards", "up"
    ],
    "loc":[
        "about", "above", "against", "along", "alongside", "amid", "among",
        "amongst", "around", "astride", "at", "athwart", "before", "behind", "below",
        "beneath", "beside", "between", "beyond", "by", "from", "in", "in_front_of",
        "inside", "near", "next_to", "off", "on", "opposite", "out_of", "outside",
        "over", "round", "throughout", "under", "underneath", "upon", "within"
    ]
}

prep["dest"] = prep["dest_conf"] + prep["dest_dir"]
prep["path"] = prep["src"] + prep["dir"] + prep["dest"]
prep["spatial"] = prep["path"] + prep["loc"]
