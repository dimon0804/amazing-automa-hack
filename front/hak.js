const tabs = document.querySelectorAll('.tab');
    const loginForm = document.getElementById('login');
    const signupForm = document.getElementById('signup');

    function setActive(tabName){
      tabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tabName));
      if(tabName === 'login'){
        loginForm.style.display = '';
        signupForm.style.display = 'none';
      } else {
        loginForm.style.display = 'none';
        signupForm.style.display = '';
      }
    }


    tabs.forEach(t => t.addEventListener('click', ()=> setActive(t.dataset.tab)));
    document.getElementById('to-signup').addEventListener('click', ()=> setActive('signup'));
    document.getElementById('to-login').addEventListener('click', ()=> setActive('login'));

    // Показ/скрытие пароля в логине
    const showLoginPw = document.getElementById('show-login-pw');
    showLoginPw.addEventListener('click', ()=>{
      const pw = document.getElementById('login-password');
      const isHidden = pw.type === 'password';
      pw.type = isHidden ? 'text' : 'password';
      showLoginPw.textContent = isHidden ? 'Скрыть' : 'Показать';
      showLoginPw.setAttribute('aria-pressed', String(isHidden));
    });

    // Симуляция отправки — замените на реальный fetch к вашему API
    loginForm.addEventListener('submit', async (e)=>{
      e.preventDefault();
      const data = {
        username: loginForm.username.value.trim(),
        password: loginForm.password.value
      };
      const msg = document.getElementById('login-msg');
      msg.textContent = 'Входим...';

      try{
        // Пример: отправка на /api/auth/login
        // const res = await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})
        // const json = await res.json();
        // Симуляция ответа
        await new Promise(r=>setTimeout(r,700));
        if(data.username === 'demo' && data.password === 'demo'){
          msg.textContent = '';
          alert('Успешный вход (симуляция)');
        } else {
          msg.textContent = 'Неверный логин или пароль';
          msg.classList.add('error');
          setTimeout(()=> msg.classList.remove('error'),3000);
        }
      }catch(err){
        msg.textContent = 'Ошибка сети';
        msg.classList.add('error');
      }
    });

    signupForm.addEventListener('submit', async (e)=>{
      e.preventDefault();
      const msg = document.getElementById('signup-msg');
      if(!document.getElementById('terms').checked){
        msg.textContent = 'Необходимо принять условия использования';
        msg.classList.add('error');
        setTimeout(()=> msg.classList.remove('error'),3000);
        return;
      }

      const payload = {
        name: signupForm.name.value.trim(),
        email: signupForm.email.value.trim(),
        password: signupForm.password.value
      };

      msg.textContent = 'Создаём аккаунт...';
      try{
        // Пример: POST /api/auth/signup
        // const res = await fetch('/api/auth/signup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
        await new Promise(r=>setTimeout(r,700));
        msg.textContent = 'Готово! Проверьте почту для подтверждения.';
        msg.classList.add('success');
        setTimeout(()=>{
          msg.classList.remove('success');
          setActive('login');
        },1400);
      }catch(err){
        msg.textContent = 'Ошибка при регистрации';
        msg.classList.add('error');
      }
    });
