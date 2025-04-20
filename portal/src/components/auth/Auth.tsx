'use client'

import config from "@/../amplify_outputs.json";
import { Authenticator } from "@aws-amplify/ui-react";
import "@aws-amplify/ui-react/styles.css";
import { Amplify } from "aws-amplify";
import React from "react";

Amplify.configure(config, { ssr: true });

const Auth = ({ children }: { children: React.ReactNode }) => {
    return (
        <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '100vh',
            width: '100%'
        }}>

            <Authenticator hideSignUp={true}>
                {children}
            </Authenticator>
        </div>);

}
export default Auth;