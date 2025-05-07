"use client"

// import type { Metadata } from "next";
import Auth from "@/components/Auth";
import {Badge, useAuthenticator} from "@aws-amplify/ui-react";
import {
    Box,
    BreadcrumbGroup,
    Container,
    ContentLayout,
    Flashbar,
    SideNavigation,
    Spinner,
    TopNavigation
} from "@cloudscape-design/components";
import AppLayout from "@cloudscape-design/components/app-layout";
import {usePathname, useRouter} from 'next/navigation';
import {useMemo, useState} from "react";
import version from '@/../package.json';


const LoadingOverlay = () => (
    <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 9999
    }}>
        <Box textAlign="center">
            <Spinner size="large"/>
            <Box variant="h3" padding="s">
                Signing out...
            </Box>
        </Box>
    </div>
);

// Navigation Component
const Navigation = () => {
    const router = useRouter();

    return (
        <SideNavigation
            header={{
                href: '/',
                text: 'Jubilee eKYC Portal',
                logo: {
                    src: '/assets/logo.svg',
                    alt: 'Jubilee eKYC Portal Logo'
                }
            }}
            items={[
                // Main Dashboard Section
                {
                    type: 'link',
                    text: 'Dashboard',
                    href: '/'
                },
                {type: "divider"},
                // KYC Operations Section
                {
                    type: 'section-group',
                    title: 'KYC Operations',
                    items: [
                        {
                            type: 'link',
                            text: 'Capture new FaceLiveness',
                            href: '/captureliveness'
                        },
                        {
                            type: 'link',
                            text: 'Upload new KYC Document',
                            href: '/uploadkycdocument'
                        }
                    ]
                },
                {type: "divider"},
                // Reports Section
                {
                    type: 'section-group',
                    title: 'Results & Analytics',
                    items: [
                        {
                            type: 'link',
                            text: 'Face Liveness Sessions',
                            href: '/liveness',
                        },
                        {
                            type: 'link',
                            text: 'KYC Documents',
                            href: '/documents',
                        },
                        {
                            type: 'link',
                            text: 'KYC Certificates',
                            href: '/certificates',
                            info: <Badge color="red" size="small">WIP</Badge>
                        }

                    ]
                },
                {type: "divider"},
                // Administration Section
                {
                    type: 'section-group',
                    title: 'Administration',

                    items: [
                        {
                            type: 'link',
                            text: 'Users',
                            href: '/users'
                        },
                        {
                            type: 'link',
                            text: 'API Calls',
                            href: '/apicalls'
                        },
                        {
                            type: 'link',
                            text: 'System Settings',
                            href: '/settings',
                            info: <Badge color="red" size="small">WIP</Badge>
                        }
                    ]
                }
            ]}
            onFollow={event => {
                event.preventDefault();
                router.push(event.detail.href);
            }}
        />
    );
};


// Create a separate component for the main layout to use hooks
function MainLayout2({
                         children,
                     }: Readonly<{
    children: React.ReactNode;
}>) {
    const {user, signOut} = useAuthenticator();
    const [navigationOpen, setNavigationOpen] = useState(true);
    const [isSigningOut, setIsSigningOut] = useState(false);
    const pathname = usePathname();
    const router = useRouter();
    const breadcrumbItems = useMemo(() => {

        const pathSegments = pathname.split('/')
            .filter((segment: string) => segment !== '');

        const items = [{text: 'Home', href: '/'}];

        let currentPath = '';
        pathSegments.forEach((segment: string) => {
            currentPath += `/${segment}`;
            items.push({
                text: segment.charAt(0).toUpperCase() + segment.slice(1),
                href: currentPath
            });
        });

        return items;
    }, [pathname]);

    const handleSignOut = async () => {
        try {
            setIsSigningOut(true);
            signOut();
        } catch (error) {
            console.error('Error signing out:', error);
        } finally {
            setIsSigningOut(false);
        }
    };

    return (
        <>
            {isSigningOut && <LoadingOverlay/>}

            <AppLayout
                navigationOpen={navigationOpen}
                onNavigationChange={({detail}) => setNavigationOpen(detail.open)}
                navigation={<Navigation/>}
                breadcrumbs={
                    <BreadcrumbGroup
                        items={breadcrumbItems}
                        onFollow={event => {
                            event.preventDefault();
                            router.push(event.detail.href);
                        }}
                    />
                }
                toolsHide={true}
                notifications={<Flashbar items={[]}/>}
                content={
                    <ContentLayout
                        header={
                            <TopNavigation
                                identity={{
                                    href: "/",
                                    title: `Jubilee eKYC Portal v${version}`,
                                    logo: {
                                        src: "/assets/logo.svg",
                                        alt: "Jubilee eKYC Portal"
                                    },
                                }}
                                utilities={[
                                    {
                                        type: "menu-dropdown",
                                        text: "",
                                        description: user?.signInDetails?.loginId || "User",
                                        iconName: "user-profile",
                                        items: [
                                            {id: "signout", text: "Sign out"}
                                        ],
                                        onItemClick: () => handleSignOut()
                                    }
                                ]}
                            />
                        }
                    >
                        <Container>
                            {children}
                        </Container>
                    </ContentLayout>
                }


            />

        </>
    );
};

export default function MainLayout({
                                       children,
                                   }: Readonly<{
    children: React.ReactNode;
}>) {
    return (<>
        <Auth>
            <MainLayout2> {children} </MainLayout2>
        </Auth>
    </>)
}