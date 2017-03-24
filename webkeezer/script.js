//var mydata = JSON.parse("tempc.json");
//console.log(data.tempC);
//var paragraph = document.getElementById("cur_temp");

//paragraph.innerHTML = " <span>"+data.tempC+"</span>";

//document.getElementById("pId").textContent=data.tempC;
//document.getElementById("cur_temp").innerHTML=data.tempC;
//var temparea = document.getElementById('disptemp');
var temptext = document.getElementById('temptext');
var setpointtext = document.getElementById('setpointtext');


timetext.innerText="Last reading at: " + data.time;
temptext.innerText="Sensor Temp: " + data.temp1C;
setpointtext.innerText="Setpoint: " + data.setpoint;
relaytext.innerText="The relay is " + ["Off", "On"][data.relayState];
temp2text.innerText="Tap Temp: " + data.temp2C;
floortext.innerText="The floor is currently " + ["nice and dry.", "FLOODED!"][data.floorState];



