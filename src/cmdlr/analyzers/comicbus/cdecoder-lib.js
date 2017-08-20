function nn(n) {
    return n < 10 ? '00' + n : n < 100 ? '0' + n : n;
}

function mm(p) {
    return (parseInt((p - 1) / 10) % 10) + (((p - 1) % 10) * 3)
}

var y = 46;

function lc(l) {
    if (l.length != 2)
        return l;
    var az = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
    var a = l.substring(0, 1);
    var b = l.substring(1, 2);
    if (a == "Z")
        return 8000 + az.indexOf(b);
    else
        return az.indexOf(a) * 52 + az.indexOf(b);
}

function su(a, b, c) {
    var e = (a + '').substring(b, b + c);
    return (e);
}

var result = {};

function ge() {
  return result;
}

function spp() {}

function getUrl(js, ch, p) {
  eval(js);
  return result.src;
}

function getPageCount(js, ch) {
  var p = 1;
  eval(js)
  return ps;
}
