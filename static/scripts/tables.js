var trs = document.getElementsByTagName('tr')

for (var i = 0; i < trs.length; i++) {
    trs[i].onclick = (event) => {
      removeAll('active-row');
      event.currentTarget.classList.add('active-row');
    };
}

const removeAll = (className) => {
  var elements = document.getElementsByClassName(className);
  for (var i = 0; i < elements.length; i++) {
    elements[i].classList.remove(className)
  }
}