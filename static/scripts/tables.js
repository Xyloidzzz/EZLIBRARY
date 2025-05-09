var trs = document.getElementsByTagName('tr');
var addForm = document.getElementById('add-form');
var editForm = document.getElementById('edit-form');

for (var i = 0; i < trs.length; i++) {
    trs[i].onclick = (event) => {
      if (!event.currentTarget.classList.contains('active-row')) {
        removeAll('active-row');
        event.currentTarget.classList.add('active-row');
        addForm.setAttribute('hidden', 'true');
        editForm.removeAttribute('hidden');
      }
      else {
        event.currentTarget.classList.remove('active-row')
        editForm.setAttribute('hidden', 'true');
        addForm.removeAttribute('hidden');
      }
    };
}

const removeAll = (className) => {
  var elements = document.getElementsByClassName(className);
  for (var i = 0; i < elements.length; i++) {
    elements[i].classList.remove(className)
  }
}