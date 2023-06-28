const axiosConfig = {
    headers: {
        "x-csrf-token": csrf
    }
};

// # => id
// 選id="loginForm"的標籤 綁定送出事件
$('#loginForm').submit(function (event) {
    // 預防表單重整畫面
    event.preventDefault();
    const form = {
        email: $('#loginEmail').val(),
        password: $('#loginPassword').val(),
    };
    console.log('[登入]', form);
    // 使用填寫的帳密登入
    firebase
        .auth()
        .signInWithEmailAndPassword(form.email, form.password)
        // 成功登入
        .then(async res => {
            console.log("成功", res);
            const idToken = await res.user.getIdToken();
            console.log("idToken", idToken);
            axios
                .post("/api/login", { id_token: idToken }, axiosConfig)
                .then(res => {
                    console.log("完成登入", res)
                    // 重整畫面
                    window.location.reload();
                })
                .catch(err => {
                    console.log("失敗", err)
                });
        })
        // 登入失敗
        .catch(err => {
            console.log("失敗", err);
            alert(err.message);
        });
});

$('#signUpForm').submit(function (event) {
    event.preventDefault();
    const form = {
        email: $('#signUpEmail').val(),
        password: $('#signUpPassword').val(),
    };
    console.log('[註冊]', form);
    // 使用填寫的帳密註冊
    firebase
        .auth()
        .createUserWithEmailAndPassword(form.email, form.password)
        // 成功註冊
        .then(async res => {
            console.log("成功", res);
            const idToken = await res.user.getIdToken();
            console.log("idToken", idToken);
            axios
                .post("/api/login", { id_token: idToken }, axiosConfig)
                .then(res => {
                    console.log("完成註冊", res)
                    // 重整畫面
                    window.location.reload();
                })
                .catch(err => {
                    console.log("失敗", err)
                });
        })
        // 註冊失敗
        .catch(err => {
            console.log("失敗", err);
            alert(err.message);
        });
});

$('#logoutBtn').click(function () {
    console.log('[登出]');
    axios
        .post("/api/logout", {}, axiosConfig)
        .then(res => {
            window.location = "/"
        })
        .catch(err => {
            window.location = "/"
        })
});