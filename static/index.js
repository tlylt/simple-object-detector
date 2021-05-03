
function getBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = (error) => reject(error);
    });
}
document.querySelector("#fileUpload").addEventListener("change", (event) => {
    handleImageUpload(event);
});

const handleImageUpload = (event) => {
    const files = event.target.files;
    getBase64(files[0]).then((data) => {
        fetch("/predict", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ image_encoded: data }),
        })
            .then((response) => response.json())
            .then((response_json) => {
                const image = document.createElement("img");
                const inference_time = document.createElement("p");
                inference_time.innerHTML = "Inference time taken: " + response_json["inference_time"].toFixed(3) + " seconds";
                image.src = response_json["image_encoded"];
                console.log(response_json["status"]);
                const container = document.querySelector("#display");
                container.innerHTML = "";
                container.appendChild(inference_time);
                container.appendChild(image);
            })
            .catch((error) => {
                console.error(error);
            });
    });
};
const handleImageUpload_file = (event) => {
    const files = event.target.files;
    const formData = new FormData();
    formData.append("image", files[0]);

    fetch("/predict_file", {
        method: "POST",
        body: formData,
    })
        .then((response) => response.blob())
        .then((image) => URL.createObjectURL(image))
        .then((imageUrl) => {
            const image = document.createElement("img");
            image.src = imageUrl;
            console.log(imageUrl);
            const container = document.querySelector("#display");
            container.innerHTML = "";
            container.appendChild(image);
        })
        .catch((error) => {
            console.error(error);
        });
};