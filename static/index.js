document.querySelector('#fileUpload').addEventListener('change', event => {
    handleImageUpload(event)
})
const handleImageUpload = event => {
    const files = event.target.files
    const formData = new FormData()
    formData.append('image', files[0])

    fetch('/predict', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            console.log(data)
        })
        .catch(error => {
            console.error(error)
        })
}
function handleSubmit() {

    const input = document.querySelector('input[type="file"]')
    console.log(input.files[0])
    const formData = new FormData();
    formData.append('image', input.files[0]);
    fetch('/predict', {
        method: 'POST',
        body: formData
    }).then(
        response => response.blob()
    ).then(
        image => URL.createObjectURL(image)
    ).then(
        imageUrl => {
            const image = document.createElement("img");
            console.log('>??');

            image.src = imageUrl;
            console.log(imageUrl)
            document.body.appendChild(image);
        }
    ).catch(console.error);
    console.log('Ok');
}
