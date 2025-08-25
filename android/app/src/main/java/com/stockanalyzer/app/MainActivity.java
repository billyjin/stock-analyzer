package com.stockanalyzer.app;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Context;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {
    
    private WebView webView;
    private ProgressBar progressBar;
    private TextView loadingText;
    private LinearLayout errorLayout;
    private Button retryButton;
    
    // Streamlit Cloud URL - 실제 배포된 URL로 변경하세요
    private static final String STREAMLIT_URL = "https://your-app-name.streamlit.app";
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        initViews();
        setupWebView();
        setupRetryButton();
        
        if (isNetworkAvailable()) {
            loadWebApp();
        } else {
            showError();
            Toast.makeText(this, "인터넷 연결을 확인해주세요", Toast.LENGTH_SHORT).show();
        }
    }
    
    private void initViews() {
        webView = findViewById(R.id.webView);
        progressBar = findViewById(R.id.progressBar);
        loadingText = findViewById(R.id.loadingText);
        errorLayout = findViewById(R.id.errorLayout);
        retryButton = findViewById(R.id.retryButton);
    }
    
    @SuppressLint("SetJavaScriptEnabled")
    private void setupWebView() {
        WebSettings webSettings = webView.getSettings();
        
        // JavaScript 활성화 (Streamlit 필요)
        webSettings.setJavaScriptEnabled(true);
        
        // 기타 설정
        webSettings.setDomStorageEnabled(true);
        webSettings.setLoadWithOverviewMode(true);
        webSettings.setUseWideViewPort(true);
        webSettings.setBuiltInZoomControls(true);
        webSettings.setDisplayZoomControls(false);
        webSettings.setSupportZoom(true);
        webSettings.setDefaultTextEncodingName("utf-8");
        
        // 캐시 설정
        webSettings.setCacheMode(WebSettings.LOAD_DEFAULT);
        webSettings.setAppCacheEnabled(true);
        
        // WebViewClient 설정
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageStarted(WebView view, String url, android.graphics.Bitmap favicon) {
                showLoading();
            }
            
            @Override
            public void onPageFinished(WebView view, String url) {
                hideLoading();
                showWebView();
            }
            
            @Override
            public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
                showError();
                Toast.makeText(MainActivity.this, "페이지 로드 오류: " + description, Toast.LENGTH_SHORT).show();
            }
        });
    }
    
    private void setupRetryButton() {
        retryButton.setOnClickListener(v -> {
            if (isNetworkAvailable()) {
                loadWebApp();
            } else {
                Toast.makeText(this, "인터넷 연결을 확인해주세요", Toast.LENGTH_SHORT).show();
            }
        });
    }
    
    private void loadWebApp() {
        showLoading();
        webView.loadUrl(STREAMLIT_URL);
    }
    
    private void showLoading() {
        progressBar.setVisibility(View.VISIBLE);
        loadingText.setVisibility(View.VISIBLE);
        webView.setVisibility(View.GONE);
        errorLayout.setVisibility(View.GONE);
    }
    
    private void hideLoading() {
        progressBar.setVisibility(View.GONE);
        loadingText.setVisibility(View.GONE);
    }
    
    private void showWebView() {
        webView.setVisibility(View.VISIBLE);
        errorLayout.setVisibility(View.GONE);
    }
    
    private void showError() {
        progressBar.setVisibility(View.GONE);
        loadingText.setVisibility(View.GONE);
        webView.setVisibility(View.GONE);
        errorLayout.setVisibility(View.VISIBLE);
    }
    
    private boolean isNetworkAvailable() {
        ConnectivityManager connectivityManager = (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);
        NetworkInfo activeNetworkInfo = connectivityManager.getActiveNetworkInfo();
        return activeNetworkInfo != null && activeNetworkInfo.isConnected();
    }
    
    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
    
    @Override
    protected void onResume() {
        super.onResume();
        webView.onResume();
    }
    
    @Override
    protected void onPause() {
        super.onPause();
        webView.onPause();
    }
    
    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.destroy();
        }
        super.onDestroy();
    }
}
