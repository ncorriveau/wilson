import React, { useState } from 'react';
import axios from 'axios';
import qs from 'qs';

interface LoginPageProps {
    setToken: (token: string, userId: string) => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ setToken }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        const data = {
            username: email,
            password: password
        };

        try {
            const response = await axios.post('http://localhost:8000/api/v1/auth/token',  
            qs.stringify(data), {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            });
            console.log("user id is: ", response.data.userId);
            setToken(response.data.access_token, response.data.userId);
        
        } catch (error) {
            setError('Invalid username or password');
        }
    };

    return (
        <div>
            <h2>Login</h2>
            <form onSubmit={handleSubmit}>
                <input
                    type="text"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Email"
                />
                <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Password"
                />
                <button type="submit">Login</button>
            </form>
            {error && <p>{error}</p>}
        </div>
    );
};

export default LoginPage;
