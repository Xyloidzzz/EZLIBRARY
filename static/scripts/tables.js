console.log("we good...");
var trs = document.getElementsByTagName('tr')
console.log(trs)

for (var i = 0; i < trs.length; i++) {
    console.log(trs[i])
    trs[i].onclick = (event) => {
      removeAll('active-row');
      event.currentTarget.classList.add('active-row');
      console.log(event.currentTarget.classList)
    };
}

const removeAll = (className) => {
  var elements = document.getElementsByClassName(className);
  for (var i = 0; i < elements.length; i++) {
    elements[i].classList.remove(className)
  }
}