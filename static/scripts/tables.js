console.log("we good...");
var trs = document.getElementsByTagName('tr')
console.log(trs)

for (var i = 0; i < trs.length; i++) {
    console.log("FUCKYOU")
    console.log(trs[i])
    trs[i].onclick = (event) => {
      alert("CLICK");
      trs[i].classList.add('active-row');
    };
}

// trs.array.forEach(element => {
//   console.log(element)
//   element.onclick = event => {
//     console.log("CLICKED")
//   }
// });

// console.log("YAY")
// document.querySelectorAll("td").forEach(
//   (e) => {
//     console.log("FUCK YOU")
//     e.addEventListener("click", () => {
//       console.log("frick you...")
//       e.classList.add('active-row')
//     })
//   }
// )