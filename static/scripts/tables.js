var trs = document.getElementsByTagName('tr')

for (var i = 0; i < trs.length; i++) {
    trs[i].onclick = (event) => {
      if (!event.currentTarget.classList.contains('active-row')) {
        removeAll('active-row');
        event.currentTarget.classList.add('active-row');
      }
      else {
        event.currentTarget.classList.remove('active-row')
      }
    };
}

const removeAll = (className) => {
  var elements = document.getElementsByClassName(className);
  for (var i = 0; i < elements.length; i++) {
    elements[i].classList.remove(className)
  }
}