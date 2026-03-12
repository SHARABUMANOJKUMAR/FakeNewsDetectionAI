// ============================
// CONFIG
// ============================

const GOOGLE_SCRIPT_URL =
"https://script.google.com/macros/s/AKfycbzgOWnIa2MyxSERznOvrMyUTp9cZZA-3RZppUmVMYhkDgxQn-cfO_d8zMrfBtAJQbgW/exec";


// ============================
// TEXT DETECTION
// ============================

async function checkNews(){

let news = document.getElementById("news").value;

if(news.trim()===""){
alert("Please enter news text");
return;
}

// Loading message
document.getElementById("result").innerText="Analyzing with AI...";
document.getElementById("explain").innerText="";

try{

let response = await fetch("/predict",{
method:"POST",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({text:news})
});

let data = await response.json();

displayResult(data);

saveToGoogleSheet(news,data,"TEXT");

}catch(err){

console.error(err);
alert("Error analyzing news");

}

}


// ============================
// URL DETECTION
// ============================

async function checkURL(){

let url = document.getElementById("url").value;

if(url.trim()===""){
alert("Please enter URL");
return;
}

document.getElementById("result").innerText="Analyzing article...";
document.getElementById("explain").innerText="";

try{

let response = await fetch("/predict_url",{
method:"POST",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({url:url})
});

let data = await response.json();

displayResult(data);

saveToGoogleSheet(url,data,"URL");

}catch(err){

console.error(err);
alert("URL analysis failed");

}

}


// ============================
// SHOW RESULT IN UI
// ============================

function displayResult(data){

document.getElementById("result").innerText = data.prediction;

document.getElementById("explain").innerText =
"Important words: " + data.explanation.join(", ");

}


// ============================
// SAVE DATA TO GOOGLE SHEETS
// ============================

async function saveToGoogleSheet(article,data,source){

let name = prompt("Enter your name:");
let email = prompt("Enter your email:");

if(!name || !email){
alert("Name and Email required for report.");
return;
}

let title = article.substring(0,80).replace(/\n/g," ");

let prediction = data.prediction.includes("Fake") ? "FAKE" : "REAL";

let payload = {

name:name,
email:email,
title:title,
article:article,
prediction:prediction,
confidence:"95%",
model:"MultinomialNB",
url: source==="URL" ? article : "Text Input"

};

try{

await fetch(GOOGLE_SCRIPT_URL,{
method:"POST",
body:JSON.stringify(payload)
});

console.log("Saved to Google Sheets");

}catch(err){

console.error("Google Sheet Error",err);

}

}