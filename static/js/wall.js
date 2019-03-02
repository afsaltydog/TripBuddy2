$(document).ready(function(){
    $('#regForm').keyup(function(){
        console.log("This is JavaScript!");
        var data = $("#regForm").serialize()   // capture all the data in the form in the variable data
        console.log("data is ",data);
        $.ajax({
            method: "POST",   // we are using a post request here, but this could also be done with a get
            url: "/email",
            data: data
        })
        .done(function(res){
             $('#emailMsg').html(res)  // manipulate the dom when the response comes back
        })
    })
    return false;
})