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
        populate_editForm(event.currentTarget);
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

const populate_editForm = (row) => {
  var inputs = editForm.getElementsByTagName('input');
  var selects = editForm.getElementsByTagName('select');
  var cells = row.getElementsByTagName('td');
  for (var i = 0; i < inputs.length; i++) {
    if (inputs[i].type === 'checkbox') {
      inputs[i].checked = cells[i].innerText === 'True' ? true : false;
    } else {
      
      inputs[i].value = cells[i].innerText;
    }
  }
  for (var i = 0; i < selects.length; i++) {
    var options = selects[i].options;
    for (var j = 0; j < options.length; j++) {
      if (options[j].value === cells[cells.length - 2].innerText) {
        options[j].selected = true;
      }
    }
  }
}